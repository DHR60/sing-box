package bridge

import (
	"net"
	"testing"

	"github.com/sagernet/netlink"
	"golang.org/x/sys/unix"
)

func TestIsDefaultDestination(t *testing.T) {
	if !isDefaultDestination(nil) {
		t.Fatal("expected nil to be default destination")
	}
	if !isDefaultDestination(&net.IPNet{IP: net.IPv6zero, Mask: net.CIDRMask(0, 128)}) {
		t.Fatal("expected ::/0 to be default destination")
	}
	if !isDefaultDestination(&net.IPNet{IP: net.IPv4zero, Mask: net.CIDRMask(0, 32)}) {
		t.Fatal("expected 0.0.0.0/0 to be default destination")
	}
	if isDefaultDestination(&net.IPNet{IP: net.ParseIP("2001:db8::"), Mask: net.CIDRMask(64, 128)}) {
		t.Fatal("expected 2001:db8::/64 not to be default destination")
	}
	if isDefaultDestination(&net.IPNet{IP: net.IPv4(192, 168, 1, 0), Mask: net.CIDRMask(24, 32)}) {
		t.Fatal("expected 192.168.1.0/24 not to be default destination")
	}
}

func TestIsIPv6GUA(t *testing.T) {
	if !isIPv6GUA(net.ParseIP("2001:db8::1")) {
		t.Fatal("expected 2001:db8::1 to be GUA")
	}
	if !isIPv6GUA(net.ParseIP("2409:8a00::1")) {
		t.Fatal("expected 2409:8a00::1 to be GUA")
	}
	if isIPv6GUA(net.ParseIP("fd00::1")) {
		t.Fatal("expected fd00::1 (ULA) not to be 2000::/3 GUA")
	}
	if isIPv6GUA(net.ParseIP("fe80::1")) {
		t.Fatal("expected fe80::1 not to be GUA")
	}
	if isIPv6GUA(net.ParseIP("192.168.1.1")) {
		t.Fatal("expected IPv4 not to be IPv6 GUA")
	}
}

func TestFilterAndSortLinkAddresses(t *testing.T) {
	candidates := []netlink.Route{
		{
			Src: &net.IPNet{IP: net.ParseIP("2409:8a00::"), Mask: net.CIDRMask(64, 128)},
		},
	}

	addrTentative := netlink.Addr{
		IPNet: &net.IPNet{IP: net.ParseIP("2001:db8::99"), Mask: net.CIDRMask(64, 128)},
		Flags: unix.IFA_F_TENTATIVE,
	}
	addrUla := netlink.Addr{
		IPNet: &net.IPNet{IP: net.ParseIP("fd12:3456::1"), Mask: net.CIDRMask(64, 128)},
	}
	addrGuaOther := netlink.Addr{
		IPNet: &net.IPNet{IP: net.ParseIP("2001:db8::1"), Mask: net.CIDRMask(64, 128)},
	}
	addrDeprecatedGua := netlink.Addr{
		IPNet: &net.IPNet{IP: net.ParseIP("2001:db8::2"), Mask: net.CIDRMask(64, 128)},
		Flags: unix.IFA_F_DEPRECATED,
	}
	addrMatchingSrc := netlink.Addr{
		IPNet: &net.IPNet{IP: net.ParseIP("2409:8a00::1234"), Mask: net.CIDRMask(64, 128)},
	}

	raw := []netlink.Addr{addrTentative, addrUla, addrGuaOther, addrDeprecatedGua, addrMatchingSrc}
	sorted := filterAndSortLinkAddresses(raw, unix.AF_INET6, candidates)

	// Tentative should be excluded
	for _, a := range sorted {
		if a.IP.Equal(addrTentative.IP) {
			t.Fatal("tentative address should be filtered out")
		}
	}
	// addrMatchingSrc should be first
	if len(sorted) != 4 || !sorted[0].IP.Equal(addrMatchingSrc.IP) {
		t.Fatalf("expected address matching candidate src to be first, got %v", sorted)
	}
	// addrGuaOther should be before addrUla
	if !sorted[1].IP.Equal(addrGuaOther.IP) {
		t.Fatalf("expected public GUA before ULA, got %v", sorted)
	}
	// addrUla before deprecated
	if !sorted[2].IP.Equal(addrUla.IP) {
		t.Fatalf("expected ULA before deprecated GUA, got %v", sorted)
	}
}

type dummyLink struct {
	attrs netlink.LinkAttrs
}

func (d *dummyLink) Attrs() *netlink.LinkAttrs {
	return &d.attrs
}

func (d *dummyLink) Type() string {
	return "dummy"
}

func TestResolveEgressDefaultRouteFromCandidates(t *testing.T) {
	link := &dummyLink{
		attrs: netlink.LinkAttrs{
			Index: 42,
			Name:  "dummy42",
		},
	}

	gw1 := net.ParseIP("fe80::1")
	gw2 := net.ParseIP("fe80::2")
	srcNet := &net.IPNet{IP: net.ParseIP("2001:db8::1"), Mask: net.CIDRMask(128, 128)}

	linkRoutes := []netlink.Route{
		// Non-default connected route - should be ignored
		{
			LinkIndex: 42,
			Table:     unix.RT_TABLE_MAIN,
			Family:    unix.AF_INET6,
			Type:      unix.RTN_UNICAST,
			Dst:       &net.IPNet{IP: net.ParseIP("fe80::"), Mask: net.CIDRMask(64, 128)},
		},
		// Local route - should be ignored
		{
			LinkIndex: 42,
			Table:     unix.RT_TABLE_LOCAL,
			Family:    unix.AF_INET6,
			Type:      unix.RTN_LOCAL,
			Dst:       &net.IPNet{IP: net.ParseIP("2001:db8::1"), Mask: net.CIDRMask(128, 128)},
		},
		// Candidate with source restriction and higher metric
		{
			LinkIndex: 42,
			Table:     unix.RT_TABLE_MAIN,
			Family:    unix.AF_INET6,
			Type:      unix.RTN_UNICAST,
			Dst:       defaultDestination(unix.AF_INET6),
			Gw:        gw2,
			Src:       srcNet,
			Priority:  1024,
		},
		// Candidate with lower metric
		{
			LinkIndex: 42,
			Table:     unix.RT_TABLE_MAIN,
			Family:    unix.AF_INET6,
			Type:      unix.RTN_UNICAST,
			Dst:       defaultDestination(unix.AF_INET6),
			Gw:        gw1,
			Priority:  100,
		},
	}

	route := resolveEgressDefaultRoute(2201, unix.AF_INET6, link, linkRoutes)
	if route == nil {
		t.Fatal("expected default route to be resolved from linkRoutes")
	}
	if route.Table != 2201 {
		t.Fatalf("expected table 2201, got %d", route.Table)
	}
	if route.LinkIndex != 42 {
		t.Fatalf("expected linkIndex 42, got %d", route.LinkIndex)
	}
	if !route.Gw.Equal(gw1) {
		t.Fatalf("expected gw1 (%s), got %s", gw1, route.Gw)
	}
	if route.Flags != int(unix.RTNH_F_ONLINK) {
		t.Fatalf("expected ONLINK flag, got %d", route.Flags)
	}
	if route.Src != nil {
		t.Fatalf("expected no source restriction on generated default route, got %s", route.Src)
	}
}

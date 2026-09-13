package process

import (
	"reflect"
	"testing"

	"github.com/sagernet/sing-box/adapter"
	"github.com/sagernet/sing-tun"
)

func TestCompleteProcessInfoAndroidPackages(t *testing.T) {
	for _, uid := range []int32{12345, 1012345} {
		info := &adapter.ConnectionOwner{
			ProcessID:   42,
			UserId:      uid,
			UserName:    "android-user",
			ProcessPath: "/system/bin/app_process64",
		}
		completeProcessInfo(info, &testProcessPackageManager{t: t})
		if want := []string{"shared.package", "app.package"}; !reflect.DeepEqual(info.AndroidPackageNames, want) {
			t.Fatalf("uid %d: packages = %v, want %v", uid, info.AndroidPackageNames, want)
		}
		if info.ProcessID != 42 || info.UserId != uid || info.UserName != "android-user" || info.ProcessPath != "/system/bin/app_process64" {
			t.Fatalf("process identity changed: %+v", info)
		}
	}
}

func TestCompleteProcessInfoPreservesExistingPackages(t *testing.T) {
	for _, unknownUID := range []bool{false, true} {
		info := &adapter.ConnectionOwner{UserId: 12345, UserName: "known-user", AndroidPackageNames: []string{"platform.package"}}
		var packageManager tun.PackageManager
		if unknownUID {
			info.UserId = -1
			packageManager = &testProcessPackageManager{t: t}
		}
		completeProcessInfo(info, packageManager)
		if !reflect.DeepEqual(info.AndroidPackageNames, []string{"platform.package"}) {
			t.Fatalf("existing package metadata lost: %+v", info)
		}
	}
}

type testProcessPackageManager struct {
	tun.PackageManager
	t *testing.T
}

func (m *testProcessPackageManager) SharedPackageByID(id uint32) (string, bool) {
	m.t.Helper()
	if id != 12345 {
		m.t.Fatalf("expected Android app ID 12345, got %d", id)
	}
	return "shared.package", true
}

func (m *testProcessPackageManager) PackagesByID(id uint32) ([]string, bool) {
	m.t.Helper()
	if id != 12345 {
		m.t.Fatalf("expected Android app ID 12345, got %d", id)
	}
	return []string{"shared.package", "app.package", "app.package"}, true
}

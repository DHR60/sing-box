package rule

import (
	"context"

	"github.com/sagernet/fswatch"
	"github.com/sagernet/sing-box/adapter"
	C "github.com/sagernet/sing-box/constant"
	"github.com/sagernet/sing-box/log"
	"github.com/sagernet/sing-box/option"
	"github.com/sagernet/sing/common"
	E "github.com/sagernet/sing/common/exceptions"
	"github.com/sagernet/sing/common/logger"
	"github.com/sagernet/sing/common/x/list"
)

var _ adapter.RuleSet = (*LocalRuleSet)(nil)

type LocalRuleSet struct {
	abstractRuleSet
	watcher   *fswatch.Watcher
	callbacks list.List[adapter.RuleSetUpdateCallback]
}

func NewLocalRuleSet(ctx context.Context, logger logger.ContextLogger, options option.RuleSet) (*LocalRuleSet, error) {
	ruleSet := &LocalRuleSet{
		abstractRuleSet: abstractRuleSet{
			ctx:    ctx,
			logger: logger,
			tag:    options.Tag,
		},
	}
	if options.Type == C.RuleSetTypeInline {
		if len(options.InlineOptions.Rules) == 0 {
			return nil, E.New("empty inline rule-set")
		}
		err := ruleSet.reloadRules(options.InlineOptions.Rules)
		if err != nil {
			return nil, err
		}
	} else {
		ruleSet.format = options.Format
		path, err := ruleSet.getPath(ctx, options.Path)
		if err != nil {
			return nil, err
		}
		ruleSet.path = path
		err = ruleSet.loadFromFile(path)
		if err != nil {
			return nil, err
		}
		watcher, err := fswatch.NewWatcher(fswatch.Options{
			Path: []string{path},
			Callback: func(path string) {
				uErr := ruleSet.loadFromFile(path)
				if uErr != nil {
					logger.ErrorContext(log.ContextWithNewID(context.Background()), E.Cause(uErr, "reload rule-set ", options.Tag))
				}
			},
		})
		if err != nil {
			return nil, err
		}
		ruleSet.watcher = watcher
	}
	return ruleSet, nil
}

func (s *LocalRuleSet) StartContext(ctx context.Context, startContext *adapter.HTTPStartContext) error {
	if s.watcher != nil {
		err := s.watcher.Start()
		if err != nil {
			s.logger.Error(E.Cause(err, "watch rule-set file"))
		}
	}
	return nil
}

func (s *LocalRuleSet) reloadRules(headlessRules []option.HeadlessRule) error {
	err := s.abstractRuleSet.reloadRules(headlessRules)
	if err != nil {
		return err
	}
	callbacks := s.callbacks.Array()
	s.access.Unlock()
	for _, callback := range callbacks {
		callback(s)
	}
	return nil
}

func (s *LocalRuleSet) PostStart() error {
	return nil
}

func (s *LocalRuleSet) RegisterCallback(callback adapter.RuleSetUpdateCallback) *list.Element[adapter.RuleSetUpdateCallback] {
	s.access.Lock()
	defer s.access.Unlock()
	return s.callbacks.PushBack(callback)
}

func (s *LocalRuleSet) UnregisterCallback(element *list.Element[adapter.RuleSetUpdateCallback]) {
	s.access.Lock()
	defer s.access.Unlock()
	s.callbacks.Remove(element)
}

func (s *LocalRuleSet) Close() error {
	s.rules = nil
	return common.Close(common.PtrOrNil(s.watcher))
}

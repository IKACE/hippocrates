from argparse import ArgumentParser
from copy import deepcopy
from enum import Enum, auto
from pathlib import Path
from IPython import embed

import collections
import re

# https://pyyaml.org/wiki/PyYAMLDocumentation
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    print(f'Could not import CLoader/CDumper, gonna be slow')
    exit(-1)
    from yaml import Loader, Dumper

class BugReportSource(Enum):
    GENERIC = auto()
    PMTEST = auto()

class TraceEvent(collections.abc.Mapping):
    '''
        Represents an event in the trace of events.
    '''

    class EventType(Enum):
        '''
            All the PM operations:
                - Store
                - Flush
                - Fence
            
            Some operations are compound:
                - MOVNT: store + flush
                - CLFLUSH: flush + LOCAL fence
        '''
        STORE = auto()
        FLUSH = auto()
        FENCE = auto()
        '''
            All the PM assertions.

                Correctness:
                    - Missing flush (universal persistency issue)
                    - Missing fence (universal ordering issue)
            
                Performance:
                    - Extraneous flush (universal persistency)
            
            There are some things which we cannot fix:

                Correctness:
                    - Semantic ordering (could cause logical side effects)
                
                Performance:
                    - Extraneous fence (could cause concurrent side effects)
        '''
        ASSERT_PERSISTED = auto()
        ASSERT_ORDERED = auto()
        REQUIRED_FLUSH = auto()

    def _validate(self):
        '''
            Ensures that the trace event has all the fields we want in it.
        '''
        assert hasattr(self, 'timestamp') and isinstance(self.timestamp, int)
        assert hasattr(self, 'event') and isinstance(self.event, self.EventType)
        assert hasattr(self, 'function') and isinstance(self.function, str)
        assert hasattr(self, 'file') and isinstance(self.file, str)
        assert hasattr(self, 'line') and isinstance(self.line, int)
        assert hasattr(self, 'is_bug') and isinstance(self.is_bug, bool)
        assert hasattr(self, 'stack') and isinstance(self.stack, list)
        for sf in self.stack:
            assert isinstance(sf, dict)
            assert 'function' in sf and isinstance(sf['function'], str)
            assert 'file' in sf and isinstance(sf['file'], str)
            assert 'line' in sf and isinstance(sf['line'], int)

        if self.event == self.EventType.STORE or \
                self.event == self.EventType.FLUSH or \
                self.event == self.EventType.ASSERT_PERSISTED or \
                self.event == self.EventType.REQUIRED_FLUSH:
            assert hasattr(self, 'address') and isinstance(self.address, int)
            assert hasattr(self, 'length') and isinstance(self.length, int)
        elif self.event == self.EventType.ASSERT_ORDERED:
            assert hasattr(self, 'address_a') and isinstance(self.address_a, int)
            assert hasattr(self, 'length_a') and isinstance(self.length_a, int)
            assert hasattr(self, 'address_b') and isinstance(self.address_b, int)
            assert hasattr(self, 'length_b') and isinstance(self.length_b, int)

    def __init__(self, original=None, **kwargs):
        if original is not None:
            self.__dict__.update(original)
        self.__dict__.update(
            {k: v for k, v in kwargs.items() if v is not None})

        if 'event' in self.__dict__:
            self.__dict__['event'] = self.EventType[self.__dict__['event']]
        
        self._validate()
    
    def __iter__(self):
        return iter(self.__dict__)
    
    def __getitem__(self, a):
        item = getattr(self, a)
        if isinstance(item, self.EventType):
            return item.name
        return item
    
    def __len__(self):
        return len(self.__dict__)


class BugReport:
    def __init__(self, output_file):
        assert isinstance(output_file, Path)
        self.output_file = output_file
        self.trace = []
        self.metadata = {}

    def set_source(self, src):
        assert(isinstance(src, BugReportSource))
        self.metadata['source'] = src.name

    def _validate_metadata(self):
        ''' Check that all the required metadata as been setup. '''
        assert ('source' in self.metadata), 'call set_source(BugReportSource)!'

    def _add_internal(self, **kwargs):
        self.trace += [kwargs]

    def add_trace_event(self, te: TraceEvent) -> None:
        self._add_internal(**te)

    def _optimize(self):
        ''' 
            Do a few things:
            1. Remove redundant bugs first.
            2. Remove everything that isn't related to a bug. 
        '''
        is_bug = lambda x: x['event'] in ['ASSERT_PERSISTED', 'ASSERT_ORDERED', 'REQUIRED_FLUSH']

        # Step 1: Remove redundancies.
        unique_bugs = []
        new_trace = []
        for te in self.trace:
            if not is_bug(te):
                new_trace += [te]
                continue

            is_unique = True
            for bug in unique_bugs:
                if te['stack'] == bug['stack']:
                    is_unique = False
                    break

            if is_unique:
                unique_bugs += [te]
                new_trace += [te]

    
        print(f'(Step 1) Optimized from {len(self.trace)} trace events to {len(new_trace)} trace events.')
        self.trace = new_trace


        # Step 2: Remove junk
        bugs = [x for x in self.trace if is_bug(x)]
        bug_addresses = []
        for bug in bugs:
            if bug['event'] == 'ASSERT_ORDERED':
                a1 = (bug['address_a'], bug['address_a'] + bug['length_a'])
                a2 = (bug['address_b'], bug['address_b'] + bug['length_b'])
                bug_addresses += [a1, a2]
            else:
                addr = (bug['address'], bug['address'] + bug['length'])
                bug_addresses += [addr]

        new_trace = []
        prev_te = None
        for te in self.trace:
            if te in bugs:
                new_trace += [te]
            elif te['event'] == 'FENCE':
                if prev_te is not None and prev_te['event'] == 'FENCE':
                    continue
                new_trace += [te]
            else:
                address_range = (te['address'], te['address'] + te['length'])
                for bug_addr in bug_addresses:
                    if bug_addr[0] < address_range[1] and address_range[0] < bug_addr[1]:
                        new_trace += [te]
                        break

            prev_te = te

        print(f'(Step 2) Optimized from {len(self.trace)} trace events to {len(new_trace)} trace events.')
        self.trace = new_trace

        
    
    def dump(self):
        self._validate_metadata()
        self._optimize()
        print(f'Prepare to dump.\n\tNum items: {len(self.trace)}')
        report = {'trace': self.trace, 'metadata': self.metadata}
        raw = yaml.dump(report, None, Dumper=Dumper)
        print('Prepare to write.')
        with self.output_file.open('w') as f:
            f.write(raw)
            # yaml.dump(report, f)
        print(f'Report written to {str(self.output_file)}')

    def __getitem__(self, a):
        return self.trace[a]

class TraceUtils:
    COLOR_RE = re.compile('\\033\[\d+m')

    @staticmethod
    def strip_color(word):
        ''' Remove the color ASCII sequence. '''
        removed = TraceUtils.COLOR_RE.sub('', word)
        return removed

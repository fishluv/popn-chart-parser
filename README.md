**Utilities for parsing pop'n music chart (.bin) files.**

### Setup

Python 3. No dependencies. If you use [pyenv](https://github.com/pyenv/pyenv) you can do `pyenv install`.

Since .bin files come from .ifs files, you will probably want [ifstools](https://github.com/mon/ifstools) globally installed.

### A brief intro to pop'n music's chart file

A .bin file can be thought of as a list of timestamped "events" where each event describes something that happens in the chart at that timestamp: a note, a bpm change, the start of a measure, etc.

Each event consists of:

1. a timestamp, in milliseconds,
2. an event id indicating the event type, and
3. either one or two numeric values depending on whether the chart uses the "old" or "new" format.

Multiple events can occur on the same timestamp.

Here are some very simplified examples. (The real files are structured the same way but the data is encoded much more tersely.)

Excerpt from V [Hyper] (old format - only one numeric value):

```
<...>
73600 measure 0
73600 key     4
73800 key     6
74000 key     1
74100 key     2
74200 key     3
74300 key     4
74400 key     5
74600 key     7
74800 key     2
74900 key     3
75000 key     4
75100 key     5
75200 measure 0
75200 key     6
<...>
```

Excerpt from IDM UPPER [Normal] (new format - two numeric values):

```
<...>
36000 measure 0 0
36000 key     7 1000
36000 key     1 0
36333 key     2 0
36666 key     3 0
37000 key     4 0
37333 measure 0 0
37333 key     1 1000
37333 key     7 0
37666 key     6 0
38000 key     5 0
38333 key     4 0
<...>
```

The first numeric value is important for some events (`key` - which button the note is for) and meaningless for others (`measure`).

The second numeric value (only present in the new format) is only used for `key` events. A nonzero value indicates that that note is a hold note and the value represents the length of the hold.

How do you know which format a chart uses? Any chart created since Usaneko (including new charts for songs from old versions) will use the new format. Older charts will use the old format.

### [parse_chart.py](parse_chart.py)

Provides a util function that parses a .bin file into events and returns a list of events with the values decoded into a more human readable format.

When run standalone, outputs the events to stdout as headerless CSV.

```
$ python parse_chart.py --bin-file v_hyper.bin --format old | head -20
0,timesig,1028,0
0,timing,118,0
0,timing,4218,0
0,timing,8318,0
0,timing,12420,0
0,timing,16520,0
0,timing,20620,0
0,bpm,150,0
0,sample2,61572,0
0,measure,0,0
0,beat,0,0
400,beat,0,0
800,beat,0,0
1200,beat,0,0
1400,sample,33,0
1400,sample,4096,0
1400,sample,8192,0
1400,sample,12288,0
1400,sample,16384,0
1400,sample,20480,0
```

### [serialize_chart.py](serialize_chart.py)

Provides a util function that, for a given .bin file, returns a subset of the events _grouped by timestamp_, as a dictionary that maps timestamp to another dictionary mapping event name to event value.

When run standalone, outputs the events to stdout as headered CSV.

```
$ python serialize_chart.py --bin-file v_hyper.bin --format old | head -20
timestamp,key,keyon,keyoff,measurebeatend,bpm
0,,,,m,150
400,,,,b,
800,,,,b,
1200,,,,b,
1600,257,,,m,
1700,4,,,,
1800,64,,,,
2000,1,,,b,
2100,2,,,,
2200,8,,,,
2400,2,,,b,
2500,8,,,,
2600,32,,,,
2800,1,,,b,
2900,4,,,,
3000,16,,,,
3200,2,,,m,
3300,8,,,,
3400,32,,,,
```

### [summarize_chart.py](summarize_chart.py)

Provides a util function that, for a given .bin file, returns a summary of the chart (note count, bpm, duration, etc.) as a dictionary.

When run standalone, outputs the summary to stdout as a JSON object.

```
$ python summarize_chart.py --bin-file v_hyper.bin --format old
{"notes":1134,"hold_notes":0,"bpm":"150","bpm_steps":[150],"duration":124,"timing":"standard","timing_steps":[[118,122,126,132,136,140]]}
```

from collections import defaultdict
from operator import itemgetter

try:
  from parse_chart import get_events
except ImportError:
  from .parse_chart import get_events

def summarize_chart(bin_filename, new_format):
  events = get_events(bin_filename, new_format)

  notes = 0
  hold_notes = 0
  min_bpm = 9999
  max_bpm = 0
  bpm_steps = []
  timesig_steps = []

  # A "frameset" is a list of 6 values defining, in order,
  # [0] start of early bad window
  # [1] start of early good window
  # [2] start of early great window
  # [3] end of late great window
  # [4] end of late good window
  # [5] end of late bad window
  # in approximate frames.
  # These "frame" values range from 104 to 154 and are used to calculate
  # the sizes of the judgment windows, in milliseconds.
  framesets_by_ts = defaultdict(lambda: [None] * 6)

  duration_ms = 0
  last_bpm = 0
  last_bpm_ts = 0
  duration_by_bpm = defaultdict(int)
  last_timesig = 0
  last_timesig_ts = 0
  duration_by_timesig = defaultdict(int)

  for timestamp, event_name, value, length in events:
    if event_name == "key":
      notes += 1
      if length > 0:
        notes += 1
        hold_notes += 1
    elif event_name in ["sample", "sample2", "timing"]:
      val1, val2 = value & 0xff, value >> 12
      if event_name == "timing":
        frame_idx, frame_val = val2, val1
        # Rarely, charts will specify multiple timings on the same timestamp.
        # Just count the most recently defined value.
        framesets_by_ts[timestamp][frame_idx] = frame_val
    elif event_name == "bpm":
      min_bpm = min(min_bpm, value)
      max_bpm = max(max_bpm, value)
      bpm_steps.append(value)
      if last_bpm:
        duration_by_bpm[last_bpm] += timestamp - last_bpm_ts
      last_bpm_ts = timestamp
      last_bpm = value
    elif event_name == "end" and not duration_ms: # charts sometimes have multiple `end`s. only use first.
      duration_ms = timestamp
    elif event_name == "timesig":
      top, bottom = value >> 8, value & 0xff
      timesig = f"{top}/{bottom}"
      timesig_steps.append(timesig)
      if last_timesig:
        duration_by_timesig[last_timesig] += timestamp - last_timesig_ts
      last_timesig_ts = timestamp
      last_timesig = timesig

  if not duration_ms:
    # A handful of charts are missing an `end` event. Just assume value from last timestamp.
    # omni/labpop_np, omni/animer_np, omni/latinpop_2nd_op
    duration_ms = events[-1][0]

  duration = duration_ms // 1000

  duration_by_bpm[last_bpm] += duration_ms - last_bpm_ts
  bpm_main, bpm_main_duration = sorted(duration_by_bpm.items(), key=itemgetter(1), reverse=True)[0]
  if bpm_main_duration == duration_ms:
    bpm_main_type = "constant"
  elif bpm_main_duration > duration_ms / 2:
    bpm_main_type = "majority"
  else:
    bpm_main_type = "nonmajority"

  duration_by_timesig[last_timesig] += duration_ms - last_timesig_ts
  timesig_main, timesig_main_duration = sorted(duration_by_timesig.items(), key=itemgetter(1), reverse=True)[0]
  if timesig_main_duration == duration_ms:
    timesig_main_type = "constant"
  elif timesig_main_duration > duration_ms / 2:
    timesig_main_type = "majority"
  else:
    timesig_main_type = "nonmajority"

  # Ensure this is sorted by timestamp.
  # (This is not guaranteed since it is possible for smaller timestamps
  # to be inserted later than larger timestamps.)
  framesets_by_ts = dict(sorted(framesets_by_ts.items()))
  framesets = list(framesets_by_ts.values())
  if len(framesets) == 1:
    timing = "standard" if framesets[0] == [118, 122, 126, 132, 136, 140] else "nonstandard"
  else:
    timing = "variable"

  return {
    "notes": notes,
    "hold_notes": hold_notes,
    "bpm": str(min_bpm) if min_bpm == max_bpm else "%s-%s" % (min_bpm, max_bpm),
    "bpm_main": bpm_main,
    "bpm_main_type": bpm_main_type,
    "bpm_steps": bpm_steps,
    "duration": duration,
    "timesig_main": timesig_main,
    "timesig_main_type": timesig_main_type,
    "timesig_steps": timesig_steps,
    "timing": timing,
    "timing_steps": framesets,
  }

"""
Usage:
  # Extract bin files from ifs first
  ifstools iidx_kida.ifs

  # Print summary to stdout
  python summarize_chart.py --bin-file iidx_kida_ifs/iidx_kida_op.bin --format new
"""
if __name__ == "__main__":
  import argparse
  import json

  parser = argparse.ArgumentParser()
  parser.add_argument("--bin-file", required=True)
  parser.add_argument("--format", help="'new' or 'old'", required=True)
  parser.add_argument("--out-file", help="Output file. If omitted, will output to stdout.")
  args = parser.parse_args()

  bin_filename = args.bin_file
  new_format = args.format == "new"
  out_filename = args.out_file

  summary = summarize_chart(bin_filename, new_format)
  summary_json = json.dumps(summary, separators=(",", ":"))

  if out_filename:
    with open(out_filename, "w") as f:
      f.write(summary_json)
  else:
    print(summary_json)

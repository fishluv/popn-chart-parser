from collections import defaultdict

from parse_chart import parse_chart

def summarize_chart(bin_filename, new_format):
  events = parse_chart(bin_filename, new_format)

  notes = 0
  hold_notes = 0
  min_bpm = 9999
  max_bpm = 0
  bpm_steps = []
  duration = 0
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

  for timestamp, event_name, value, length in events:
    if event_name in ["key", "timesig"]:
      val1, val2 = value & 0xff, value >> 8
      value = "%s/%s" % (val1, val2)
      if event_name == "key":
        notes += 1
        if length > 0:
          notes += 1
          hold_notes += 1
    elif event_name in ["sample", "sample2", "timing"]:
      val1, val2 = value & 0xff, value >> 12
      value = "%s/%s" % (val1, val2)
      if event_name == "timing":
        frame_idx, frame_val = val2, val1
        # Rarely, charts will specify multiple timings on the same timestamp.
        # Just count the most recently defined value.
        framesets_by_ts[timestamp][frame_idx] = frame_val
    elif event_name == "bpm":
      min_bpm = min(min_bpm, value)
      max_bpm = max(max_bpm, value)
      bpm_steps.append(value)
    elif event_name == "end" and not duration: # charts sometimes have multiple `end`s. only use first.
      duration = timestamp // 1000

  if not duration:
    # A handful of charts are missing an `end` event. Just assume value from last timestamp.
    # omni/labpop_np, omni/animer_np, omni/latinpop_2nd_op
    last_timestamp = events[-1][0]
    duration = last_timestamp // 1000

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
    "bpm_steps": bpm_steps,
    "duration": duration,
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
  args = parser.parse_args()

  bin_filename = args.bin_file
  new_format = args.format == "new"

  summary = summarize_chart(bin_filename, new_format)

  print(json.dumps(summary, separators=(",", ":")))
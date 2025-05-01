from parse_chart import get_events

"""
Outputs a log of keysounds played for a chart.

Usage:
  python debug_keysounds.py --bin-file sorasumi_op.bin
"""
if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("--bin-file", required=True)
  parser.add_argument("--no-source", action="store_true")
  parser.add_argument("--no-zero", action="store_true")
  parser.add_argument("--sort-in-timestamp", action="store_true")
  args = parser.parse_args()

  bin_file = args.bin_file
  no_source = args.no_source
  no_zero = args.no_zero
  sort_in_timestamp = args.sort_in_timestamp

  played_samples = []
  loaded_keysound_for_key = [0, 0, 0, 0, 0, 0, 0, 0, 0]
  for timestamp, event_name, event_value, _ in get_events(bin_file):
    if event_name == "key":
      key = event_value
      if no_zero and loaded_keysound_for_key[key] == 0:
        continue
      played_samples.append(((timestamp, loaded_keysound_for_key[key], "key%s" % key)))

    if event_name == "loadsample" and event_value & 0xff != 0:
      key, sample_idx = event_value >> 12, event_value & 0xff
      loaded_keysound_for_key[key] = sample_idx

    if event_name == "playsample":
      sample_idx = event_value & 0xff
      if no_zero and sample_idx == 0: # rare and idk why but it happens
        continue
      played_samples.append((timestamp, sample_idx, "playsample"))

  if sort_in_timestamp:
    played_samples.sort()
  
  for timestamp, sample_idx, source in played_samples:
    if no_source:
      print(timestamp, sample_idx)
    else:
      print(timestamp, sample_idx, source)

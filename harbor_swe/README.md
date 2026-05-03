## SWE Image Warmup

This directory contains the Harborized public SWE task packages (`swe_0` through `swe_99`), shared runtime assets, and helper scripts for resolving task images.

`warmup_images.sh` resolves SWE task images in this order:

1. Use an existing local Docker image if it is already present.
2. If `HILBENCH_SWE_IMAGE_ARCHIVE_ROOT` is set, load `images/<attempt_id>.tar.zst` from that local archive tree.
3. Otherwise download the archive from the configured HF bucket with `hf buckets cp` and `docker load` it.

The default bucket lives in `shared/image_source_defaults.json`. To test a future namespace before regenerating task metadata, set `HILBENCH_SWE_HF_BUCKET`, for example:

```bash
export HILBENCH_SWE_HF_BUCKET="kellu-scale/hil-bench-swe-images"
```

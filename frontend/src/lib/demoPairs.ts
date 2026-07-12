// Bundled fallback for the demo-pair list, mirroring GET /demo/pairs on the
// deployed backend (same ids, same damage-ranked order).
//
// Why it exists: the dropdown used to stay empty until a /health probe
// succeeded, so during a free-tier cold start (or any backend restart) there
// was nothing to click and the demo was dead in the water. The pair list is
// static content shipped in this repo's data/demo — there is no reason to
// gate it on a network round-trip. The live list still replaces this the
// moment the backend answers, so a changed demo set wins once it's reachable;
// analyze/image requests to a waking Render host are held by its proxy until
// boot completes, so a demo started from this fallback still works.
import type { DemoPair } from "./api";

export const FALLBACK_DEMO_PAIRS: DemoPair[] = [
  {
    id: "mexico-earthquake_00000076",
    disaster_type: "earthquake",
    pre_image: "mexico-earthquake_00000076_pre_disaster.png",
    post_image: "mexico-earthquake_00000076_post_disaster.png",
  },
  {
    id: "mexico-earthquake_00000006",
    disaster_type: "earthquake",
    pre_image: "mexico-earthquake_00000006_pre_disaster.png",
    post_image: "mexico-earthquake_00000006_post_disaster.png",
  },
  {
    id: "midwest-flooding_00000008",
    disaster_type: "flood",
    pre_image: "midwest-flooding_00000008_pre_disaster.png",
    post_image: "midwest-flooding_00000008_post_disaster.png",
  },
  {
    id: "midwest-flooding_00000011",
    disaster_type: "flood",
    pre_image: "midwest-flooding_00000011_pre_disaster.png",
    post_image: "midwest-flooding_00000011_post_disaster.png",
  },
  {
    id: "midwest-flooding_00000006",
    disaster_type: "flood",
    pre_image: "midwest-flooding_00000006_pre_disaster.png",
    post_image: "midwest-flooding_00000006_post_disaster.png",
  },
  {
    id: "midwest-flooding_00000000",
    disaster_type: "flood",
    pre_image: "midwest-flooding_00000000_pre_disaster.png",
    post_image: "midwest-flooding_00000000_post_disaster.png",
  },
  {
    id: "mexico-earthquake_00000005",
    disaster_type: "earthquake",
    pre_image: "mexico-earthquake_00000005_pre_disaster.png",
    post_image: "mexico-earthquake_00000005_post_disaster.png",
  },
  {
    id: "mexico-earthquake_00000010",
    disaster_type: "earthquake",
    pre_image: "mexico-earthquake_00000010_pre_disaster.png",
    post_image: "mexico-earthquake_00000010_post_disaster.png",
  },
  {
    id: "mexico-earthquake_00000012",
    disaster_type: "earthquake",
    pre_image: "mexico-earthquake_00000012_pre_disaster.png",
    post_image: "mexico-earthquake_00000012_post_disaster.png",
  },
  {
    id: "midwest-flooding_00000004",
    disaster_type: "flood",
    pre_image: "midwest-flooding_00000004_pre_disaster.png",
    post_image: "midwest-flooding_00000004_post_disaster.png",
  },
];

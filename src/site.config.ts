/**
 * All site-wide settings live here. Edit this file, nothing else,
 * to change contact details, social links, or analytics.
 */
export const SITE = {
  title: "Leon Ross",
  description:
    "Leon Ross — MPhil Computational Biology at Cambridge. ML for perturbation biology, drug target discovery, and early-stage startups.",
  url: "https://leonross.me",

  // Email is split into two parts so the raw address never appears
  // verbatim in the source or the built HTML (it is entity-encoded at
  // build time). Change both parts if the address changes.
  emailUser: "leon2ross9",
  emailDomain: "gmail.com",

  linkedin: "https://www.linkedin.com/in/leon-ross",
  github: "https://github.com/leonross-blip",

  // Shown on the Contact page.
  openTo:
    "Open to: ML x biology research collaborations, internships in techbio, and conversations with early-stage founders.",

  // Privacy-friendly analytics via GoatCounter (https://www.goatcounter.com).
  // Leave empty ("") to keep analytics off. To enable, create a GoatCounter
  // account and put your site code here, e.g. "leonross" for
  // https://leonross.goatcounter.com — the tracking script is only
  // included when this value is non-empty.
  goatCounterCode: "",
};

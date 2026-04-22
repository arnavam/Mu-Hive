"""
src/scraping/curate.py
======================
Event processing: dedup, classification, priority scoring,
IG assignment, smart filling, and top-N selection.
"""

import re

# ──────────────────────────────────────────────────────────
# 2A — MASTER_IGS (exact µLearn names, character-perfect)
# ──────────────────────────────────────────────────────────

MASTER_IGS = [
    "Cyber Security",
    "Generative AI",
    "Web Development",
    "Product Management",
    "Devops",
    "Game Dev",
    "No Or Low Code",
    "Entrepreneurship",
    "Ar Vr Mr",
    "Ui Ux",
    "Mobile Development",
    "Data Analytics",
    "Space",
    "Ai",
    "Comics",
    "Digital Marketing",
    "MuV",
    "Data Structures and Algorithm",
    "Human Resources",
    "Blockchain",
    "Data Science",
    "Project Management",
    "Quantum Computing",
    "Strategic Leadership",
    "Civil",
    "Internet Of Things (IOT) And Robotics",
    "Creative Design",
    "Beckn",
    "Quality Assurance",
    "General Tech"
]

# ──────────────────────────────────────────────────────────
# 2B — RARE IGs (these and ONLY these can use extended pool)
# ──────────────────────────────────────────────────────────

RARE_IGS = [
    "Quantum Computing",
    "Beckn",
    "Space",
    "Civil",
    "Comics"
]

# ──────────────────────────────────────────────────────────
# 2C — IG_KEYWORDS (complete, production-ready dictionary)
# ──────────────────────────────────────────────────────────

IG_KEYWORDS = {
  "Web Development": [
    "web", "frontend", "backend", "fullstack", "full stack",
    "react", "node", "django", "flask", "html", "css",
    "javascript", "typescript", "nextjs", "vue", "php", "api", "rest", "graphql",
    "weboreel", "web auction", "web app", "website",
    "web dev", "browser", "web application", "web3 frontend",
    "http", "web development", "frontend developer", "backend developer"
  ],

  "Ai": [
    "artificial intelligence", " ai ",
    "ai challenge", "neural network", "deep learning",
    "computer vision", "ai agent", "autonomous ai",
    "ai platform", "intelligent system", "ai solution",
    "ai tool", "ai build", "ai for", "aiventra",
    "fusionhack", "synapse sprint", "code innovation",
    "ai autonomous", "ai model", "ai powered", "ai driven",
    "ai x ", "ai-powered", "ai based", "using ai",
    "machine intelligence", "machine learning", " ml ",
    "nlp", "transformer", "inference", "model fine tuning", "turing"
  ],

  "Generative AI": [
    "generative", "llm", "gpt", "diffusion",
    "text-to-image", "stable diffusion", "prompt engineering",
    "genai", "gemini", "openai", "llama", "mistral",
    "image generation", "chatbot", "foundation model",
    "pixel gemini", "gen ai", "conversational ai",
    "language model", "creative ai", "generative model",
    "multimodal", "text generation"
  ],

  "Data Science": [
    "data science", "datathon", "eda", "pandas",
    "statistics", "dataset", "jupyter", "kaggle",
    "neurologic", "nlp datathon", "data contest",
    "data driven", "big data", "etl", "data pipeline",
    "data engineer", "data analyst", "data science contest",
    "nlp", "natural language processing", "scikit learn", "feature engineering"
  ],

  "Data Analytics": [
    "data analytics", "data visualization", "analytics",
    "business intelligence", "dashboard", "tableau",
    "power bi", "decode display", "visualization challenge",
    "data insight", "reporting", "metrics", "data story",
    "chart challenge", "data challenge", "data display",
    "bi challenge", "analytics hackathon"
  ],

  "Data Structures and Algorithm": [
    "data structures", "algorithm", "competitive programming",
    "cp contest", "codeforces", "leetcode", "coding contest",
    "lockout", "1v1 programming", "programming tournament",
    "codesprint", "code race", "dsa", "dynamic programming",
    "graph algorithm", "binary search", "cp individual",
    "cp team", "invariant cp", "impulse cp",
    "algorithmic", "coding challenge"
  ],

  "Cyber Security": [
    "cyber", "security", "ctf", "capture the flag",
    "vulnerability", "pentest", "bug bounty",
    "ethical hacking", "cybersecurity", "cyberwar",
    "infosec", "hacking", "exploit", "forensics",
    "malware", "network security", "penetration",
    "scbc", "vikingshacks", "secure bharat",
    "cyber nexus", "information security", "devsecops", "owasp", "siem",
    "threat intelligence", "incident response", "soc analyst"
  ],

  "Blockchain": [
    "blockchain", "web3", "smart contract", "nft",
    "defi", "solidity", "crypto", "ethereum", "polygon",
    "aetherax", "decentralized", "token", "wallet",
    "dao", "dapp", "bitcoin", "codeblue", "box box",
    "web 3", "blockzen", "crypto finance", "fintech", "finance", "banking", "payments", "digital wallet",
    "consensus", "distributed ledger", "evm", "onchain", "layer 2"
  ],

  "Game Dev": [
    "game", "game jam", "unity", "unreal", "pygame",
    "game dev", "game design", "pixel forge", "2d game",
    "3d game", "gaming", "indie game", "game engine",
    "level design", "pihacks", "game hackathon",
    "game build", "game challenge", "gamejam"
  ],

  "Ui Ux": [
    "ui", "ux", "ui/ux", "figma", "wireframe",
    "prototype", "design thinking", "user experience",
    "interface design", "designathon", "crowdera",
    "uci design", "product design", "user interface",
    "user research", "accessibility", "hci",
    "interaction design", "ux design", "visual ux",
    "usability", "design sprint"
  ],

  "Ar Vr Mr": [
    "augmented reality", "virtual reality", " ar ", " vr ",
    "ar/vr", " xr ", "metaverse", "mixed reality",
    "spatial computing", "pacific portal", "designxr",
    "immersive", "oculus", "hololens", "extended reality",
    "3d immersive", "hologram", "ar mr", "vr mr",
    "spatial experience", "immersive tech"
  ],

  "Internet Of Things (IOT) And Robotics": [
    "iot", "internet of things", "hardware", "raspberry pi",
    "arduino", "robotics", "embedded", "sensors",
    "microcontroller", "nirmith hardware", "smart device",
    "firmware", "circuit", "physical computing", "wearable",
    "automation hardware", "krithoathon", "lorri",
    "iot hackathon", "hardware hack", "hardware and software",
    "drone", "robot", "mechatronics"
  ],

  "Mobile Development": [
    "android", "ios", "flutter", "react native",
    "mobile app", "swift", "kotlin", "mobile development",
    "mobile hack", "app development", "cross platform",
    "mobile ui", "grizzly hacks",
    "zervehack", "mobile application", "mobile challenge",
    "mobile first"
  ],

  "Devops": [
    "devops", "ci/cd", "docker", "deployment",
    "pipeline", "jenkins", "gitops", "monitoring",
    "sre", "platform engineering", "helm", "ansible",
    "infrastructure as code", "site reliability",
    "build pipeline", "containerization", "kubernetes",
    "cloud infra", "cloud", "aws", "azure", "gcp", "developer week",
    "devops challenge", "cloud ops", "terraform", "observability", "prometheus", "grafana"
  ],

  "Product Management": [
    "product management", "product manager", "product strategy",
    "product thinking", "product teardown", "ai product",
    "roadmap", "product sprint",
    "product challenge", "pm challenge", "vibeflow",
    "kindly labs", "spec driven", "product build",
    "product design challenge", "product innovation"
  ],

  "Project Management": [
    "project management", "project manager", "pmp",
    "agile", "scrum", "sprint planning",
    "project challenge", "delivery management",
    "waterfall", "project strategy", "project lead",
    "project solution", "project innovation",
    "project planning", "project execution", "project dev", "project development"
  ],

  "Entrepreneurship": [
    "startup", "ideathon", "pitch", "venture",
    "business plan", "entrepreneurship", "innovation challenge",
    "katz school", "ideation", "buildathon", "founder",
    "incubation", "social enterprise", "mvp challenge",
    "smart horizon",
    "entrepreneurship simulation", "build your business",
    "startup weekend", "innovation sprint",
    "social good", "sustainable innovation", "impact startup", "climate startup",
    "startup funding", "seed", "pitch deck", "business model"
    , "women in tech", "shebuilds", "she builds"
  ],

  "Digital Marketing": [
    "marketing", "seo", "campaigns", "social media",
    "content marketing", "growth hacking", "brand",
    "digital marketing", "ai marketing", "marketing intern",
    "influencer", "advertising", "email marketing",
    "marketing challenge", "market strategy",
    "digital campaign", "growth challenge"
  ],

  "No Or Low Code": [
    "no code", "low code", "nocode", "lowcode",
    "no-code", "low-code", "bubble", "webflow",
    "zapier", "airtable", "glide", "appsmith",
    "trae", "vibe coding", "drag and drop",
    "visual programming", "no or low code",
    "no code hackathon", "low code challenge",
    "citizen developer", "visual builder"
  ],

  "Human Resources": [
    "human resources", " hr ", "people management",
    "talent", "recruitment", "hiring challenge",
    "workforce", "hr challenge",
    "people ops", "employee", "hrtech",
    "talent management", "people analytics",
    "hr innovation"
  ],

  "Strategic Leadership": [
    "strategic", "leadership", "strategy", "management hack",
    "business strategy", "case study", "case competition",
    "business challenge", "consulting", "business model",
    "strategic thinking", "decision making", "corporate hack",
    "business leadership", "management challenge",
    "executive", "strategic innovation",
    "social impact", "sustainability", "climate leadership", "community impact",
    "policy", "sdg", "impact leadership"
  ],

  "Civil": [
    "civil", "construction", "structural", "geotechnical",
    "transportation engineering", "water resources",
    "civil engineering", "bridge design", "building design",
    "urban infrastructure", "environmental engineering",
    "civil hackathon", "architecture engineering",
    "hydrohackathon", "water", "sanitation",
    "eco", "sustainable", "climate", "environment", "green", "social good"
  ],

  "Quality Assurance": [
    "quality assurance", " qa ", "testing", "test automation",
    "software testing", "quality control", "bug hunt",
    "defect", "selenium", "test case", "qa hackathon",
    "quality challenge", "code quality", "qa challenge",
    "testing hackathon", "quality engineering"
  ],

  "Comics": [
    "comics", "comic", "manga", "illustration",
    "storytelling", "graphic novel", "cartoon",
    "storyboard", "visual storytelling", "comic hack",
    "animation challenge", "sketch challenge",
    "drawing challenge", "comic creation",
    "webcomic", "digital art story"
  ],

  "MuV": [
    "media", "visual arts", "short film", "reel",
    "storytelling", "content creation",
    "acting", "performance", "stage", "theatre",
    "filmmaking", "podcast", "photography challenge",
    "vlog", "screenplay", "documentary",
    "spoken word", "art performance", "video challenge",
    "film festival", "content creator"
  ],

  "Space": [
    "space", "satellite", "nasa", "aerospace", "orbital",
    "rocketry", "astrophysics", "spacetech", "cosmos",
    "space exploration", "lunar", "mars", "telescope",
    "space challenge", "isro", "space innovation", "space mission"
  ],

  "Quantum Computing": [
    "quantum", "qubit", "qiskit", "quantum circuit",
    "quantum ml", "quantum computing", "quantum hackathon",
    "superposition", "entanglement", "quantum algorithm",
    "quantum challenge", "quantum innovation",
    "quantum software", "quantum physics"
  ],

  "Creative Design": [
    "creative design", "illustration", "visual design",
    "branding", "graphic design", "motion design",
    "photography", "design challenge",
    "typography", "poster design", "logo design",
    "art challenge", "creative challenge", "design sprint",
    "visual communication", "design competition"
  ],

  "Beckn": [
    "beckn", "ondc", "open network", "interoperability",
    "decentralized commerce", "beckn protocol",
    "open commerce", "network protocol",
    "beckn challenge", "open protocol", "beckn build"
  ],

  "General Tech": []
}

# ──────────────────────────────────────────────────────────
# 2D — assign_best_ig() WITH MuV STRICT GUARD
# ──────────────────────────────────────────────────────────

def _normalized_matching_text(event):
  """Build normalized multi-field text for IG matching."""
  text = (
    f"{event.get('eventName', '')} "
    f"{event.get('description', '')} "
    f"{event.get('platform', '')}"
  ).lower()
  return re.sub(r"[^a-z0-9+\s]", " ", text)


def _keyword_hit(text: str, keyword: str) -> bool:
  k = keyword.strip().lower()
  if not k:
    return False

  # Multi-word terms are checked as phrase matches; single-word terms as word boundaries.
  if " " in k or "+" in k:
    return k in text

  prefix_terms = {"eco"}
  if k in prefix_terms:
    return k in text

  return re.search(rf"\b{re.escape(k)}\b", text) is not None


def _compute_ig_scores(event, IG_KEYWORDS):
  text = _normalized_matching_text(event)
  scores = {}

  negative_signals = {
    "Cyber Security": {
      "terms": ["eco", "sustainable", "sustainability", "climate", "environment", "green", "social good"],
      "penalty": 2,
    }
  }

  for ig, keywords in IG_KEYWORDS.items():
    if ig == "General Tech":
      continue
    positive_score = sum(1 for keyword in keywords if _keyword_hit(text, keyword))
    penalty_conf = negative_signals.get(ig)
    if penalty_conf:
      negatives = penalty_conf["terms"]
      penalty = penalty_conf["penalty"] * sum(1 for term in negatives if _keyword_hit(text, term))
      positive_score = max(0, positive_score - penalty)
    scores[ig] = positive_score

  return text, scores


def _top_two_scores(scores: dict[str, int]) -> tuple[int, int]:
  ordered = sorted(scores.values(), reverse=True)
  top = ordered[0] if ordered else 0
  second = ordered[1] if len(ordered) > 1 else 0
  return top, second


def _is_confident_assignment(best_score: int, second_score: int) -> bool:
  """Keep assignments high precision: clear winner or clearly strong signal."""
  if best_score <= 0:
    return False
  if best_score >= 3:
    return True
  return (best_score - second_score) >= 1


def assign_best_ig(event, IG_KEYWORDS):
  text, scores = _compute_ig_scores(event, IG_KEYWORDS)

  best_ig = None
  best_score = 0
  for ig, score in scores.items():
    if score > best_score:
      best_score = score
      best_ig = ig

  # ── MuV STRICT GUARD ──────────────────────────────────
  # MuV = creative/media IG. Never assign tech events.
  if best_ig == "MuV":
    muv_required = [
      "media", "film", "story", "content creator",
      "creative", "video", "acting", "performance",
      "reel", "animation", "podcast", "photography",
      "stage", "theatre", "screenplay", "vlog",
      "filmmaking", "short film", "documentary"
    ]
    if not any(word in text for word in muv_required):
      best_ig = "General Tech"
      best_score = 0
  # ──────────────────────────────────────────────────────

  top_score, second_score = _top_two_scores(scores)
  if not _is_confident_assignment(top_score, second_score):
    return "General Tech", 0, scores

  if best_score <= 0:
    return "General Tech", 0, scores

  return best_ig, best_score, scores


def infer_event_type(event):
  """Infer the event type from title/description using the required priority order."""
  title = str(event.get("eventName", "")).lower()
  desc = str(event.get("description", "")).lower()
  tags = event.get("tags", [])
  if isinstance(tags, list):
    tags_text = " ".join(str(tag) for tag in tags).lower()
  else:
    tags_text = str(tags).lower()

  text = f"{title} {desc} {tags_text}"

  type_keywords = [
    ("Hackathon", ["hackathon", "hack sprint", "hackfest", "hack day", "buildathon", "sprint"]),
    ("Bootcamp", ["bootcamp", "boot camp"]),
    ("Workshop", ["workshop", "hands-on", "masterclass"]),
    ("Contest", ["contest", "competition", "challenge", "coding contest", "quiz"]),
  ]

  for event_type, keywords in type_keywords:
    if any(keyword in text for keyword in keywords):
      return event_type

  return "Hackathon"


def compute_score(event):
    score = 0
    days  = event.get("days_remaining", 999)

    # Date proximity
    if   days <= 3:  score += 100
    elif days <= 7:  score += 70
    elif days <= 10: score += 40
    else:            score += 20   # extended pool events

    # Event type
    etype = str(event.get("_event_type", event.get("eventType", ""))).lower()
    if   "hackathon" in etype: score += 80
    elif "bootcamp"  in etype: score += 50
    elif "contest"   in etype: score += 30
    elif "workshop"  in etype: score += 20

    # Location
    loc = event.get("location", "").lower()
    if "online" in loc or "virtual" in loc: score += 40
    elif "kerala" in loc:                   score += 35

    # Cost
    if "free" in event.get("cost", "").lower(): score += 30

    return score

RELATED_IGS = {
    "Ai":                                    ["Generative AI", "Data Science", "Web Development"],
    "Generative AI":                         ["Ai", "Data Science", "Creative Design"],
    "Data Science":                          ["Data Analytics", "Ai", "Data Structures and Algorithm"],
    "Data Analytics":                        ["Data Science", "Ai", "Data Structures and Algorithm"],
    "Data Structures and Algorithm":         ["Data Science", "Cyber Security", "General Tech"],
    "Cyber Security":                        ["Data Structures and Algorithm", "Devops", "General Tech"],
    "Blockchain":                            ["Web Development", "Cyber Security", "Devops"],
    "Game Dev":                              ["Creative Design", "Mobile Development", "Ar Vr Mr"],
    "Ui Ux":                                 ["Creative Design", "Web Development", "Mobile Development"],
    "Ar Vr Mr":                              ["Game Dev", "Creative Design", "Mobile Development"],
    "Internet Of Things (IOT) And Robotics": ["Space", "Devops", "Cyber Security"],
    "Mobile Development":                    ["Web Development", "Ui Ux", "Game Dev"],
    "Devops":                                ["Web Development", "Cyber Security", "General Tech"],
    "Project Management":                    ["Product Management", "Strategic Leadership", "Entrepreneurship"],
    "Product Management":                    ["Project Management", "Entrepreneurship", "Digital Marketing"],
    "Entrepreneurship":                      ["Product Management", "Strategic Leadership", "Digital Marketing"],
    "Digital Marketing":                     ["Entrepreneurship", "Product Management", "General Tech"],
    "No Or Low Code":                        ["Web Development", "Mobile Development", "General Tech"],
    "Human Resources":                       ["Strategic Leadership", "Entrepreneurship", "General Tech"],
    "Strategic Leadership":                  ["Project Management", "Entrepreneurship", "General Tech"],
    "Civil":                                 ["Space", "Internet Of Things (IOT) And Robotics", "General Tech"],
    "Quality Assurance":                     ["Devops", "Data Structures and Algorithm", "General Tech"],
    "Comics":                                ["Creative Design", "Ui Ux", "General Tech"],
    "Space":                                 ["Internet Of Things (IOT) And Robotics", "Ai", "General Tech"],
    "Quantum Computing":                     ["Ai", "Data Science", "General Tech"],
    "Creative Design":                       ["Ui Ux", "Game Dev", "Comics"],
    "Beckn":                                 ["Web Development", "Devops", "General Tech"],
    "Web Development":                       ["Mobile Development", "Ui Ux", "General Tech"],
    "General Tech":                          [],
    "MuV":                                   ["Creative Design", "Comics", "Ui Ux"]
}

def curate(primary_events, extended_events, IG_KEYWORDS):
  # ──────────────────────────────────────────────────────────
  # 2E — GLOBAL DEDUPLICATION (run before anything else)
  # ──────────────────────────────────────────────────────────

  unique_events = {}
  for event in list(primary_events or []) + list(extended_events or []):
    link = str(event.get("registrationLink", "")).strip()
    if not link or link in unique_events:
      continue
    unique_events[link] = event

  all_events = list(unique_events.values())

  # ──────────────────────────────────────────────────────────
  # 2F — SINGLE-PASS SCORING AND IG ASSIGNMENT
  # ──────────────────────────────────────────────────────────

  grouped = {ig: [] for ig in MASTER_IGS}

  for event in all_events:
    link = str(event.get("registrationLink", "")).strip()
    if not link:
      continue

    event_type = infer_event_type(event)
    event["eventType"] = event_type
    event["_event_type"] = event_type
    event["score"] = compute_score(event)
    event["_score"] = event["score"]
    if "days_remaining" in event and "_days_remaining" not in event:
      event["_days_remaining"] = event.get("days_remaining")
    if "days_remaining" in event and "_days_away" not in event:
      event["_days_away"] = event.get("days_remaining")

    ig, match_score, ig_scores = assign_best_ig(event, IG_KEYWORDS)

    event["_best_ig"] = ig
    event["_match_score"] = match_score
    event["_ig_scores"] = ig_scores
    grouped[ig].append(event)

  # ──────────────────────────────────────────────────────────
  # 2G — CONTROLLED RELATED-IG FALLBACK FOR EMPTY GROUPS
  # ──────────────────────────────────────────────────────────

  for target_ig in MASTER_IGS:
    if grouped[target_ig] or target_ig == "General Tech":
      continue

    for source_ig in RELATED_IGS.get(target_ig, []):
      source_events = grouped.get(source_ig, [])
      if len(source_events) <= 1:
        continue

      candidates = sorted(
        source_events,
        key=lambda event: (
          -event.get("_ig_scores", {}).get(target_ig, 0),
          event.get("days_remaining", 999),
          -event.get("score", 0),
        ),
      )

      moved = False
      for candidate in candidates:
        target_score = candidate.get("_ig_scores", {}).get(target_ig, 0)
        candidate_scores = candidate.get("_ig_scores", {})
        candidate_best = max(candidate_scores.values()) if candidate_scores else 0
        if target_score <= 0:
          continue
        if target_score < candidate_best:
          continue

        grouped[source_ig].remove(candidate)
        candidate["_best_ig"] = target_ig
        candidate["_match_score"] = target_score
        grouped[target_ig].append(candidate)
        moved = True
        break

      if moved:
        break

  # Secondary fallback: for still-empty IGs, borrow the closest relevant event globally.
  for target_ig in MASTER_IGS:
    if grouped[target_ig] or target_ig == "General Tech":
      continue

    global_candidates = []
    for source_ig, source_events in grouped.items():
      if source_ig != "General Tech":
        continue
      for event in source_events:
        target_score = event.get("_ig_scores", {}).get(target_ig, 0)
        candidate_scores = event.get("_ig_scores", {})
        candidate_best = max(candidate_scores.values()) if candidate_scores else 0
        if target_score > 0 and target_score == candidate_best:
          global_candidates.append((source_ig, event, target_score))

    if not global_candidates:
      continue

    source_ig, candidate, _ = sorted(
      global_candidates,
      key=lambda item: (
        -item[2],
        item[1].get("days_remaining", 999),
        -item[1].get("score", 0),
      ),
    )[0]

    grouped[source_ig].remove(candidate)
    grouped[target_ig].append(candidate)

  # ──────────────────────────────────────────────────────────
  # 2H — SORT AND CAP AT TOP 5 PER IG
  # ──────────────────────────────────────────────────────────

  for ig in MASTER_IGS:
    grouped[ig].sort(
      key=lambda x: (
        x.get("days_remaining", 999),
        -x.get("_match_score", 0),
        -x.get("score", 0),
      )
    )
    grouped[ig] = grouped[ig][:5]

  return grouped

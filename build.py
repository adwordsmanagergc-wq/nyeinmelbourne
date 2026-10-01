#!/usr/bin/env python3
"""Static site generator for NYE in Melbourne.

Edit data/events.json (and the CONFIG block below), then run:
    python3 build.py
The complete site is written to ./docs, which Vercel serves as-is (see vercel.json).
"""
import json
import shutil
from datetime import date
from html import escape
from pathlib import Path

# --------------------------------------------------------------------------------------
# CONFIG: change these before going live
# --------------------------------------------------------------------------------------
CONFIG = {
    "site_name": "NYE in Melbourne",
    "site_url": "https://nyeinmelbourne.com",   # your live domain, no trailing slash
    "contact_email": "aj@metatapdigital.com",
    "listing_price": 599,                              # AUD, inc GST
    # Listing submissions are emailed to contact_email via FormSubmit (no account needed;
    # the first submission sends a one-time activation email to that inbox).
    "form_endpoint": "https://formsubmit.co/ajax/aj@metatapdigital.com",
    # Stripe Payment Link (or similar) for the $599 listing fee. While it still contains
    # "YOUR_", submitters see a thank-you message and you email them an invoice instead.
    "payment_link": "https://buy.stripe.com/YOUR_PAYMENT_LINK",
    "year": 2026,
    "next_year": 2027,
}

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
EVENTS = json.loads((ROOT / "data" / "events.json").read_text())
TODAY = date.today().isoformat()
Y, NY = CONFIG["year"], CONFIG["next_year"]
URL = CONFIG["site_url"]

CATEGORY_LABELS = {
    "party": "Parties",
    "dining": "Dinners",
    "fine-dining": "Fine dining",
    "cruise": "Cruises",
    "rooftop": "Rooftops",
    "yarra": "Riverside",
    "family": "Family-friendly",
    "budget": "Under $250",
    "vantage": "Vantage points",
    "free": "Free",
    "bay": "Bayside",
}
AREAS = sorted({e["area"] for e in EVENTS})

NAV = [
    ("/", "Home"),
    ("/#directory", "All events"),
    ("/new-years-eve-dinner-melbourne/", "Dinners"),
    ("/new-years-eve-cruises-melbourne/", "Cruises"),
    ("/new-years-eve-parties-melbourne/", "Parties"),
    ("/melbourne-fireworks-vantage-points/", "Vantage points"),
    ("/plan-your-night/", "Plan"),
]


def j(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1).replace("</", "<\\/")


def money(n):
    return "Free" if n == 0 else f"${n:,.0f}"


SKYLINE = """<svg class="skyline" viewBox="0 0 1440 230" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
<defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c0a26"/><stop offset="1" stop-color="#07061a"/></linearGradient>
<linearGradient id="wt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a1450" stop-opacity=".9"/><stop offset="1" stop-color="#07061a"/></linearGradient></defs>
<g fill="url(#sk)">
<rect x="0" y="120" width="40" height="80"/><rect x="44" y="96" width="34" height="104"/><rect x="82" y="130" width="28" height="70"/>
<rect x="114" y="70" width="40" height="130"/><rect x="158" y="108" width="30" height="92"/><rect x="192" y="86" width="26" height="114"/>
<rect x="222" y="124" width="36" height="76"/><path d="M300 200 L318 30 L336 200Z"/><rect x="316" y="10" width="4" height="22"/>
<rect x="350" y="140" width="60" height="60"/><rect x="416" y="100" width="34" height="100"/><rect x="456" y="62" width="30" height="138"/>
<rect x="492" y="118" width="40" height="82"/><rect x="560" y="60" width="36" height="140"/><rect x="600" y="34" width="30" height="166"/>
<rect x="636" y="90" width="40" height="110"/><rect x="680" y="14" width="34" height="186"/><rect x="718" y="70" width="30" height="130"/>
<rect x="752" y="100" width="44" height="100"/><rect x="800" y="76" width="34" height="124"/><rect x="838" y="40" width="38" height="160"/>
<rect x="880" y="110" width="30" height="90"/><rect x="914" y="84" width="40" height="116"/><rect x="958" y="22" width="30" height="178"/>
<rect x="992" y="96" width="36" height="104"/><rect x="1032" y="58" width="32" height="142"/><rect x="1068" y="120" width="40" height="80"/>
<rect x="1112" y="88" width="30" height="112"/><rect x="1146" y="130" width="44" height="70"/><rect x="1194" y="72" width="34" height="128"/>
<rect x="1232" y="112" width="40" height="88"/><rect x="1290" y="110" width="38" height="90"/>
<rect x="1332" y="84" width="30" height="116"/><rect x="1366" y="126" width="40" height="74"/><rect x="1410" y="100" width="30" height="100"/>
</g>
<rect x="680" y="14" width="34" height="18" fill="#ffc94d" opacity=".35"/>
<rect x="0" y="198" width="1440" height="32" fill="url(#wt)"/>
</svg>"""


def countdown(mini=False):
    units = [("d", "Days"), ("h", "Hours"), ("m", "Minutes"), ("s", "Seconds")]
    inner = "".join(
        f'<div class="cd-unit"><div class="cd-num" data-u="{k}">--</div><div class="cd-label">{v}</div></div>'
        for k, v in units
    )
    return f'<div class="countdown{" mini" if mini else ""}" data-countdown role="timer" aria-label="Countdown to midnight, New Year\'s Eve {Y} in Melbourne">{inner}</div>'


def layout(path, title, description, body, schema=None, og_type="website", active=None):
    canonical = URL + path
    schemas = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": CONFIG["site_name"],
            "url": URL + "/",
            "potentialAction": {
                "@type": "SearchAction",
                "target": URL + "/?q={search_term_string}#directory",
                "query-input": "required name=search_term_string",
            },
        }
    ] if path == "/" else []
    schemas += schema or []
    cur = ' aria-current="page"'
    nav = "".join(
        f'<li><a href="{h}"{cur if h == (active or path) else ""}>{t}</a></li>' for h, t in NAV
    )
    ld = "".join(f'<script type="application/ld+json">{j(s)}</script>' for s in schemas)
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="geo.region" content="AU-VIC"><meta name="geo.placename" content="Melbourne">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{CONFIG['site_name']}">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{URL}/og.png"><meta property="og:locale" content="en_AU">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{URL}/og.png">
<meta name="theme-color" content="#07061a">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="nav"><div class="wrap">
<a class="logo" href="/">NYE <span>in Melbourne</span></a>
<nav aria-label="Main"><ul>{nav}</ul></nav>
<a class="btn btn-primary btn-sm" href="/list-your-event/">List your event</a>
<button class="menu-btn" aria-label="Menu" aria-expanded="false">☰</button>
</div></header>
<main id="main">
{body}
</main>
<footer><div class="wrap">
<div class="fgrid">
<div><a class="logo" href="/">NYE <span>in Melbourne</span></a>
<p class="muted">The independent guide to New Year's Eve {Y} in Melbourne: fireworks vantage points, Yarra River cruises, dinners and parties, all in one place.</p>
{countdown(mini=True)}</div>
<div><h4>Explore</h4><ul>
<li><a href="/#directory">All NYE events</a></li><li><a href="/new-years-eve-dinner-melbourne/">NYE dinners</a></li>
<li><a href="/new-years-eve-cruises-melbourne/">NYE cruises</a></li><li><a href="/new-years-eve-parties-melbourne/">NYE parties</a></li>
<li><a href="/family-new-years-eve-melbourne/">Family NYE</a></li></ul></div>
<div><h4>Plan</h4><ul>
<li><a href="/melbourne-fireworks-vantage-points/">Vantage points</a></li><li><a href="/plan-your-night/">Fireworks times</a></li>
<li><a href="/plan-your-night/#transport">Transport</a></li><li><a href="/#faq">FAQ</a></li></ul></div>
<div><h4>Venues</h4><ul>
<li><a href="/list-your-event/">List your event: ${CONFIG['listing_price']}</a></li>
<li><a href="mailto:{CONFIG['contact_email']}">{CONFIG['contact_email']}</a></li></ul></div>
</div>
<p class="fine">NYE in Melbourne is an independent guide and is not affiliated with the City of Melbourne or the official Melbourne New Year's Eve event. Prices and details are supplied by venues or based on published information and may change. Always confirm with the venue before booking. We acknowledge the Wurundjeri Woi-wurrung and Bunurong peoples of the Kulin Nation, the Traditional Owners of the land and waters on which Melbourne stands. © {Y} {CONFIG['site_name']}.</p>
</div></footer>
<script src="/main.js" defer></script>
</body>
</html>"""


# --------------------------------------------------------------------------------------
# Components
# --------------------------------------------------------------------------------------
def card(e, i):
    cats = " ".join(e["categories"])
    search = " ".join([e["name"], e["venue"], e["suburb"], e["area"], " ".join(e["categories"]), e["blurb"]]).lower()
    tags = "".join(f'<span class="tag">{CATEGORY_LABELS.get(c, c)}</span>' for c in e["categories"][:3])
    price = e["price_from"]
    price_html = (
        "Free<small>check entry details</small>" if price == 0
        else f"{money(price)}<small>from, per person</small>" if price
        else "TBA<small>see venue</small>"
    )
    return f"""<article class="card{' featured' if e.get('featured') else ''}" data-cats="{cats}" data-area="{escape(e['area'])}" data-price="{price if price is not None else ''}" data-featured="{1 if e.get('featured') else 0}" data-order="{i}" data-search="{escape(search)}">
{'<span class="badge">Featured</span>' if e.get('featured') else ''}
<div class="loc">📍 {escape(e['suburb'] if e['suburb'] in e['area'] else e['suburb'] + ' · ' + e['area'])}</div>
<h3><a href="/events/{e['slug']}/">{escape(e['name'])}</a></h3>
<p>{escape(e['blurb'])}</p>
<div class="tags"><span class="tag fw">🎆 {escape(e['fireworks'])}</span>{tags}</div>
<div class="meta"><div class="price">{price_html}</div>
<div class="actions"><a class="btn btn-ghost btn-sm" href="/events/{e['slug']}/">Details</a><a class="btn btn-primary btn-sm" href="{e['url']}" target="_blank" rel="noopener sponsored">Book</a></div></div>
</article>"""


def directory(events, heading, sub, show_filters=True, anchor="directory"):
    used = []
    for e in events:
        for c in e["categories"]:
            if c not in used:
                used.append(c)
    order = [c for c in CATEGORY_LABELS if c in used]
    chips = '<button class="chip" data-cat="all" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" data-cat="{c}" aria-pressed="false">{CATEGORY_LABELS[c]}</button>' for c in order
    )
    areas = '<option value="all">All areas</option>' + "".join(
        f'<option>{escape(a)}</option>' for a in AREAS if any(e["area"] == a for e in events)
    )
    filters = f"""<div class="filters" role="group" aria-label="Filter by type">{chips}</div>
<div class="toolbar"><input id="q" type="search" placeholder="Search venue, suburb, vibe…" aria-label="Search events">
<select id="area" aria-label="Filter by area">{areas}</select>
<select id="sort" aria-label="Sort"><option value="featured">Sort: Featured</option><option value="low">Price: low to high</option><option value="high">Price: high to low</option></select></div>
<p class="count" aria-live="polite"></p>""" if show_filters else ""
    cards = "".join(card(e, i) for i, e in enumerate(events))
    return f"""<section id="{anchor}" data-directory><div class="wrap">
<div class="section-head"><h2>{heading}</h2><p>{sub}</p></div>
{filters}
<div class="grid">{cards}</div>
<p class="empty">No events match that search. Try another filter, or <a href="/list-your-event/">list yours</a>.</p>
</div></section>"""


def season_section(p):
    months = [
        ("October", "Planning begins",
         "Big parties, cruises and rooftops release tickets, and Melbourne starts searching \"NYE in Melbourne\". Early birds lock in their plans and groups start comparing options.",
         "List now and you're live for the whole season, from day one."),
        ("November", "Comparing &amp; booking",
         "Searchers compare prices, inclusions and fireworks views side by side. This is when premium tables, cruises and party tickets get booked.",
         "Your page, with its price, inclusions and a Book button, wins the comparison."),
        ("December", "Peak searches &amp; last-minute rush",
         "Search interest hits its peak. People chase the last tables, final release tiers and late tickets right up to 31 December.",
         "Sell your remaining tickets and late seatings while demand is at its highest."),
    ]
    cards = "".join(
        f'''<div class="card season-card"><span class="season-step">{i + 1}</span><div class="loc">{m}</div><h3>{t}</h3><p>{d}</p>
<p class="season-win">✦ {w}</p></div>''' for i, (m, t, d, w) in enumerate(months)
    )
    return f"""<section id="season"><div class="wrap">
<div class="section-head"><span class="eyebrow">The NYE search season</span>
<h2>Melbourne books New Year's Eve in <span class="grad">three months</span></h2>
<p>Every year, searches like "NYE in Melbourne", "Melbourne New Year's Eve" and "New Year's Eve dinner Melbourne" climb from October and peak in the final weeks of December. That's when people choose a venue and buy tickets. If your event isn't in front of them then, they book somewhere else.</p></div>
<div class="season-bar" aria-hidden="true"><span style="--h:34%">Oct</span><span style="--h:62%">Nov</span><span style="--h:100%">Dec</span></div>
<p class="muted" style="text-align:center;font-size:.8rem;margin:-6px 0 30px">Shows the typical seasonal pattern of search interest, not exact volumes.</p>
<div class="grid">{cards}</div>
<div class="band" style="margin-top:40px">
<div><h2>One listing. The whole season.</h2><p>At typical riverside NYE prices of $150–$350 a head, a handful of bookings covers your ${p} listing. Everything after that is profit, with zero commission.</p></div>
<a class="btn" href="#form">Claim your spot →</a></div>
</div></section>"""


def list_band():
    return f"""<section><div class="wrap"><div class="band">
<div><h2>Selling NYE tickets in Melbourne?</h2><p>October to December is when Melbourne searches for its New Year's Eve plans. Get your event in front of them for ${CONFIG['listing_price']} flat, with no commission.</p></div>
<a class="btn" href="/list-your-event/">List your event →</a></div></div></section>"""


def item_list(events, name):
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "numberOfItems": len(events),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{URL}/events/{e['slug']}/", "name": e["name"]}
            for i, e in enumerate(events)
        ],
    }


def breadcrumbs(*pairs):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": URL + p} for i, (n, p) in enumerate(pairs)
        ],
    }


# --------------------------------------------------------------------------------------
# Content: FAQ, timeline, vantage points
# --------------------------------------------------------------------------------------
FAQ = [
    (f"What time are the Melbourne New Year's Eve fireworks in {Y}?",
     f"Based on recent years, there are two displays on Thursday 31 December {Y}: family-friendly fireworks at 9:30pm and the main fireworks at midnight to welcome {NY}. In 2025 the midnight show used fireworks and lasers on 27 rooftops across the city skyline, designed to be seen from all over Melbourne. The City of Melbourne confirms the {Y} program closer to the night."),
    ("Where is the best place to watch the Melbourne fireworks?",
     "The City of Melbourne's free Celebration Zones (Docklands, Kings Domain, Treasury Gardens and Flagstaff Gardens in 2025) have entertainment, food trucks and good views of both shows. Federation Square, Birrarung Marr and the Southbank Promenade put you on the river but get very crowded. Further out, Ruckers Hill in Northcote, St Kilda foreshore and Williamstown give skyline views with more space. See our <a href=\"/melbourne-fireworks-vantage-points/\">Melbourne fireworks vantage points</a> guide."),
    ("Are the Melbourne NYE fireworks free to watch?",
     "Yes. The City of Melbourne's fireworks and Celebration Zones are free and need no booking. Because the midnight fireworks launch from rooftops across the skyline, you can also watch for free from parks, hills and beaches with a clear view of the CBD. Paid options such as rooftop parties, riverside dinners, cruises and the Melbourne Skydeck give you a guaranteed spot."),
    ("How much does a New Year's Eve cruise in Melbourne cost?",
     "NYE cruises on the Yarra River and from Docklands range from about $125 for a short family twilight cruise timed for the 9:30pm fireworks, to around $209 for a midnight-only cruise, $230 to $375 for party cruises with drinks, and about $575 for a four-course dinner cruise. Smaller boats and dinner cruises sell out first. Compare them on our <a href=\"/new-years-eve-cruises-melbourne/\">NYE cruises in Melbourne</a> page."),
    ("Where can I have dinner with a fireworks view in Melbourne?",
     f"Southbank and South Wharf are the best bets for a riverside table: Ludlow, BearBrass, P.J. O'Brien's, Hophaus and Ruby Riviera all run NYE menus, and Strato on level 40 looks across the whole skyline. Early sittings are cheaper and family-friendly. See our <a href=\"/new-years-eve-dinner-melbourne/\">NYE dinners in Melbourne</a> list."),
    ("What time should I arrive at a free vantage point?",
     "The Celebration Zones opened at 6pm in 2025, and riverside spots like Southbank Promenade, Federation Square and Birrarung Marr get very busy by 8pm. Several Yarra bridges and city streets close to pedestrians during the evening, so plan your route and arrive well before the 9:30pm fireworks."),
    ("Is public transport free on New Year's Eve in Melbourne?",
     "In 2025, all Victorian public transport was free from 6pm on New Year's Eve until 6am on New Year's Day, with extra trains, trams and buses running all night. Flinders Street and Southern Cross stations stayed open all night, while Parliament, Flagstaff and Melbourne Central were open until 3am. Check ptv.vic.gov.au for the confirmed 2026 arrangements closer to the date."),
    ("Can I bring alcohol to the Melbourne fireworks?",
     "No, not to the official event. The City of Melbourne's New Year's Eve is an alcohol-free event and fines apply, so the Celebration Zones are alcohol-free. Other councils set their own rules: Footscray Park's event is alcohol-free, and St Kilda's foreshore has a glass ban. Licensed venues, cruises and parties are the way to have a drink."),
    ("What are the best family-friendly NYE options in Melbourne?",
     "The 9:30pm fireworks are made for kids. The free Celebration Zones have family entertainment, food trucks and accessible toilets, Footscray Park runs its own 9:30pm fireworks with lost-kids wristbands, and there are family twilight cruises and early dinner sittings with kids' prices at Ludlow, BearBrass, Byblós and Ruby Riviera."),
    ("Is NYE in Melbourne the official Melbourne New Year's Eve website?",
     "No. NYE in Melbourne is an independent guide and event directory. The official event is produced by the City of Melbourne at nye.melbourne.vic.gov.au. We bring together official information and bookable dinners, cruises and parties so you can plan the whole night in one place."),
    ("How do I list my New Year's Eve event on NYE in Melbourne?",
     f"It's a one-off ${CONFIG['listing_price']} fee with no commission. Your event gets its own optimised page, a place in our directory and category pages, and a direct link to your booking page. <a href=\"/list-your-event/\">List your event here</a>."),
]


def faq_html(items):
    return "".join(f"<details><summary>{escape(q)}</summary><p>{a}</p></details>" for q, a in items)


def faq_schema(items):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items
        ],
    }


TIMELINE = [
    ("Afternoon", "Road closures begin around the CBD from about 4pm, and access to the Docklands Victoria Harbour Promenade is restricted (2025)."),
    ("6:00pm", "Free public transport starts statewide. The Celebration Zones open with DJs, silent discos, dance workshops and food trucks."),
    ("7:00pm", "Northbank and Southbank pedestrian bridges and Sandridge Bridge close for the night (2025)."),
    ("9:30pm", "Family fireworks, made for kids and early nights."),
    ("10:30pm", "Swanston Street from Hamer Hall to Collins Street, including Princes Bridge, and parts of Flinders Street close to pedestrians (2025)."),
    ("Midnight", f"The midnight fireworks and lasers launch from rooftops across the city skyline to welcome {NY}."),
    ("1:00am", "Celebration Zones close. Allow time for the crowds to clear."),
    ("Until 6:00am", "Free public transport keeps running. Flinders Street and Southern Cross stay open all night (2025)."),
]


def timeline_html():
    return '<div class="timeline">' + "".join(
        f'<div class="tl"><b>{t}</b><p>{d}</p></div>' for t, d in TIMELINE
    ) + "</div>"


VANTAGE = [
    ("Docklands (Victoria Harbour)", "Docklands", "Fireworks over the harbour and skyline", "zone", "Official Celebration Zone; alcohol-free; promenade access restricted from 4pm (2025)"),
    ("Kings Domain", "Beside the Royal Botanic Gardens", "City skyline from the south", "zone", "Official Celebration Zone; grassy slopes"),
    ("Treasury Gardens", "East Melbourne", "Eastern edge of the CBD", "zone", "Official Celebration Zone; food trucks and bands"),
    ("Flagstaff Gardens", "West Melbourne", "Northern edge of the CBD", "zone", "Official Celebration Zone; the city's oldest park"),
    ("Federation Square", "Melbourne CBD", "Right in the middle of the city", "free", "Free DJs and both fireworks shows; very crowded"),
    ("Birrarung Marr", "Beside the Yarra", "River reflections", "free", "Expect heavy crowds"),
    ("Southbank Promenade & Queensbridge Square", "Southbank", "River and skyline", "free", "Very busy; arrive by 8pm"),
    ("Alexandra Gardens", "Southbank", "Across the Yarra to the city", "free", "Close to Princes Bridge closures; plan your exit"),
    ("Melbourne Skydeck", "Southbank, level 88", "Above the rooftop fireworks", "paid", "Ticketed party with drinks; book ahead"),
    ("Ruckers Hill", "Northcote", "Elevated, uninterrupted skyline", "free", "Local favourite; bring a rug"),
    ("Edinburgh Gardens", "Fitzroy North", "Distant skyline", "check", "Check City of Yarra alcohol rules for the night"),
    ("St Kilda foreshore", "St Kilda", "Skyline across the bay", "check", "Glass banned; check Port Phillip alcohol rules"),
    ("Williamstown Beach & The Strand", "Williamstown", "Skyline across Hobsons Bay", "check", "Quieter; council alcohol-free zones apply"),
    ("Footscray Park", "Footscray", "Its own 9:30pm fireworks", "free", "Alcohol- and pet-free family event"),
]
PILL = {
    "free": '<span class="pill free">Free</span>',
    "zone": '<span class="pill free">Free · official zone</span>',
    "paid": '<span class="pill paid">Paid ticket</span>',
    "check": '<span class="pill af">Free · check rules</span>',
}


def vantage_table(rows=None):
    rows = rows or VANTAGE
    body = "".join(
        f"<tr><td><b>{n}</b></td><td>{a}</td><td>{v}</td><td>{PILL[t]}</td><td class='muted'>{note}</td></tr>"
        for n, a, v, t, note in rows
    )
    return f"""<div class="table-wrap"><table><thead><tr><th>Vantage point</th><th>Area</th><th>View</th><th>Entry</th><th>Good to know</th></tr></thead>
<tbody>{body}</tbody></table></div>"""


# --------------------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------------------
def page_home():
    featured = [e for e in EVENTS if e.get("featured")]
    rest = [e for e in EVENTS if not e.get("featured")]
    ordered = featured + rest
    n = len(EVENTS)
    body = f"""
<section class="hero"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap">
<span class="eyebrow">Thursday 31 December {Y} · Melbourne</span>
<h1>Melbourne New Year's Eve {Y}<br><span class="grad">fireworks, parties &amp; dinners</span></h1>
<p class="lead">The best NYE events in Melbourne in one place: Yarra River cruises, fireworks dinners, rooftop parties and every free vantage point. Compare, choose and book your night to welcome {NY}.</p>
{countdown()}
<p class="cd-note">until the midnight fireworks over Melbourne</p>
<div class="cta-row"><a class="btn btn-primary" href="#directory">Browse {n} NYE events</a><a class="btn btn-ghost" href="/melbourne-fireworks-vantage-points/">Free vantage points</a></div>
</div></section>

<div class="wrap"><div class="facts">
<div class="fact"><b>9:30pm</b><span>Family fireworks, made for kids</span></div>
<div class="fact"><b>Midnight</b><span>Fireworks and lasers from rooftops across the city</span></div>
<div class="fact"><b>Free</b><span>public transport from 6pm (2025), plus free Celebration Zones</span></div>
<div class="fact"><b>{n}</b><span>bookable dinners, cruises, parties &amp; free events</span></div>
</div></div>

{directory(ordered, f"Every Melbourne NYE {Y} event in one directory", "Filter by type, area or budget. Every listing shows what's included, which fireworks you'll see and a direct booking link.")}

{list_band()}

<section class="alt"><div class="wrap two">
<div><h2>Your NYE {Y} in Melbourne, <span class="grad">hour by hour</span></h2>
<p class="muted">Timings are based on the 2025 event and are confirmed by the City of Melbourne closer to the night. Use this to plan when to arrive, eat and move.</p>
<a class="btn btn-ghost" href="/plan-your-night/">Full planning guide →</a></div>
{timeline_html()}
</div></section>

<section><div class="wrap">
<div class="section-head"><h2>Best fireworks vantage points</h2><p>Official Celebration Zones, riverside spots and suburban hills and beaches to watch the Melbourne fireworks, with what you need to know about each one.</p></div>
{vantage_table(VANTAGE[:8])}
<p style="text-align:center;margin-top:24px"><a class="btn btn-ghost" href="/melbourne-fireworks-vantage-points/">See all vantage points →</a></p>
</div></section>

<section class="alt"><div class="wrap">
<div class="section-head"><h2>Find your kind of NYE</h2></div>
<div class="grid">
<div class="card"><h3><a href="/new-years-eve-dinner-melbourne/">🍽️ NYE dinners with fireworks views</a></h3><p>From $110 pub dinners at Southgate to fine dining at Society and Maison Bâtard.</p><a href="/new-years-eve-dinner-melbourne/">Browse dinners →</a></div>
<div class="card"><h3><a href="/new-years-eve-cruises-melbourne/">🛥️ Yarra River &amp; Docklands NYE cruises</a></h3><p>From a $125 family twilight cruise to four-course dinner cruises at midnight.</p><a href="/new-years-eve-cruises-melbourne/">Browse cruises →</a></div>
<div class="card"><h3><a href="/new-years-eve-parties-melbourne/">🎉 NYE parties &amp; rooftops</a></h3><p>Rooftop at QT, Riverland, the Skydeck and New Year's at the Bowl.</p><a href="/new-years-eve-parties-melbourne/">Browse parties →</a></div>
<div class="card"><h3><a href="/family-new-years-eve-melbourne/">👨‍👩‍👧 Family-friendly NYE</a></h3><p>9:30pm fireworks, free Celebration Zones, Footscray Park and family cruises.</p><a href="/family-new-years-eve-melbourne/">Browse family events →</a></div>
</div></div></section>

<section id="faq"><div class="wrap">
<div class="section-head"><h2>Melbourne New Year's Eve {Y}: FAQ</h2></div>
<div class="faq">{faq_html(FAQ)}</div>
</div></section>
"""
    return layout(
        "/",
        f"New Year's Eve Melbourne {Y}: Fireworks, Parties & Dinners | NYE in Melbourne",
        f"Plan New Year's Eve {Y} in Melbourne: live countdown, fireworks times (9:30pm & midnight), free vantage points and {n} bookable NYE dinners, Yarra cruises and parties.",
        body,
        schema=[item_list(ordered, f"Melbourne New Year's Eve {Y} events"), faq_schema(FAQ),
                {"@context": "https://schema.org", "@type": "Organization", "name": CONFIG["site_name"], "url": URL + "/",
                 "logo": URL + "/favicon.svg", "email": CONFIG["contact_email"]}],
    )


CATEGORY_PAGES = [
    {
        "path": "/new-years-eve-dinner-melbourne/",
        "filter": lambda e: "dining" in e["categories"] or "fine-dining" in e["categories"],
        "title": f"New Year's Eve Dinner Melbourne {Y}: Restaurants with Fireworks Views",
        "h1": f"New Year's Eve dinners in Melbourne {Y}",
        "desc": f"The best New Year's Eve dinners in Melbourne {Y}: riverside restaurants on Southbank and South Wharf with fireworks views, family sittings, fine dining and set menus, with prices and booking links.",
        "intro": "A riverside table is the most comfortable way to see in the new year: no crowds to fight, and a long dinner while you wait for midnight. Early sittings are cheaper and often family-friendly, while late sittings take you through to the midnight fireworks.",
        "tips": ["Book early. Riverside tables on Southbank and South Wharf go first.", "Early sittings are the best-value option and many welcome kids.", "Ask whether your table has a view of the fireworks or only the venue does.", "Allow extra travel time: streets and Yarra bridges close during the evening."],
    },
    {
        "path": "/new-years-eve-cruises-melbourne/",
        "filter": lambda e: "cruise" in e["categories"],
        "title": f"New Year's Eve Cruises Melbourne {Y}: Yarra River & Docklands Fireworks Cruises",
        "h1": f"New Year's Eve cruises in Melbourne {Y}",
        "desc": f"Compare New Year's Eve cruises in Melbourne for {Y}: Yarra River dinner cruises, party cruises, a family twilight cruise for the 9:30pm fireworks and Docklands boats to the bay.",
        "intro": "Being on the water means a front-row seat without the crowds on the banks. Yarra River cruises board at Southbank Promenade or Federation Wharf, while Docklands boats can head out towards Williamstown and the bay. Most are timed for the midnight fireworks, and one family cruise lines up with the 9:30pm show.",
        "tips": ["Check the boarding point and check-in time: boats leave on time.", "Plan your trip home, as bridges and streets near the river close.", "Most party and midnight cruises are 18+. Check before booking for families.", "Dinner cruises sell out early, so book well ahead."],
    },
    {
        "path": "/new-years-eve-parties-melbourne/",
        "filter": lambda e: "party" in e["categories"] or "rooftop" in e["categories"],
        "title": f"Melbourne NYE Parties {Y}: Best New Year's Eve Parties & Rooftop Bars",
        "h1": f"The best New Year's Eve parties in Melbourne {Y}",
        "desc": f"Melbourne's best New Year's Eve parties for {Y}: rooftop bars, riverside all-inclusive parties, the Skydeck and New Year's at the Bowl, with prices, inclusions and tickets.",
        "intro": "From rooftops in the CBD to bars on the Yarra and a full festival at the Sidney Myer Music Bowl, these are the best NYE parties in Melbourne. Because the midnight fireworks launch from rooftops all over the city, a high terrace or a riverside bar can give you a great view.",
        "tips": ["Many parties release tickets in tiers, so early bird is cheapest.", "Check whether drinks are all-inclusive or pay as you go.", "Most parties are 18+ with ID checks.", "Look for venues that promise fireworks views if the view matters to you."],
    },
    {
        "path": "/family-new-years-eve-melbourne/",
        "filter": lambda e: "family" in e["categories"] or "vantage" in e["categories"],
        "title": f"Family New Year's Eve Melbourne {Y}: Kid-Friendly NYE & 9:30pm Fireworks",
        "h1": f"Family-friendly New Year's Eve in Melbourne {Y}",
        "desc": f"Kid-friendly ways to celebrate New Year's Eve {Y} in Melbourne: the 9:30pm family fireworks, free Celebration Zones, Footscray Park, family cruises and early dinner sittings.",
        "intro": "The 9:30pm fireworks are designed for kids, so you can see a full show and be home before midnight. The free Celebration Zones are alcohol-free with entertainment, food trucks and accessible toilets, which makes a big difference with little ones.",
        "tips": ["Aim for the 9:30pm fireworks with younger kids.", "The Celebration Zones are alcohol-free and family-focused.", "Pack hats, sunscreen, water, a picnic rug and ear protection for little ones.", "Agree on a meeting point in case anyone gets separated."],
    },
]


def page_category(c):
    events = [e for e in EVENTS if c["filter"](e)]
    events.sort(key=lambda e: (not e.get("featured"), e["price_from"] if e["price_from"] is not None else 1e9))
    tips = "".join(f"<li>{t}</li>" for t in c["tips"])
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">NYE {Y} · Melbourne</span><h1>{c['h1']}</h1>
<p class="lead">{c['intro']}</p>{countdown(mini=True)}</div></section>
<section style="padding-bottom:0"><div class="wrap two">
<div class="panel"><h2 style="font-size:1.5rem">Booking tips</h2><ul class="ticks">{tips}</ul></div>
<div><h2 style="font-size:1.5rem">{len(events)} options, compared</h2><p class="muted">Every listing shows a "from" price, what's included and which fireworks you'll see. Prices are per person and based on published packages, so always confirm the current price with the venue.</p>
<a class="btn btn-primary" href="/list-your-event/">Add your venue: ${CONFIG['listing_price']}</a></div>
</div></section>
{directory(events, c['h1'], 'Filter and sort to find your night.')}
{list_band()}"""
    return layout(
        c["path"], c["title"] + " | NYE in Melbourne", c["desc"], body,
        schema=[item_list(events, c["h1"]), breadcrumbs(("Home", "/"), (c["h1"], c["path"]))],
    )


def page_event(e):
    path = f"/events/{e['slug']}/"
    inc = "".join(f"<li>{escape(x)}</li>" for x in e["includes"])
    cats = ", ".join(CATEGORY_LABELS.get(c, c) for c in e["categories"])
    related = [x for x in EVENTS if x["slug"] != e["slug"] and (x["area"] == e["area"] or set(x["categories"]) & set(e["categories"]))][:3]
    offer = {"@type": "Offer", "url": e["url"], "priceCurrency": "AUD", "availability": "https://schema.org/InStock",
             "validFrom": f"{Y}-01-01"}
    if e["price_from"] is not None:
        offer["price"] = e["price_from"]
    schema = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": f"{e['name']} – New Year's Eve {Y}",
        "description": e["blurb"] + " Includes: " + "; ".join(e["includes"]) + ".",
        "startDate": f"{Y}-12-31",
        "endDate": f"{NY}-01-01",
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "image": [f"{URL}/og.png"],
        "location": {
            "@type": "Place", "name": e["venue"],
            "address": {"@type": "PostalAddress", "addressLocality": e["suburb"], "addressRegion": "VIC", "addressCountry": "AU"},
        },
        "organizer": {"@type": "Organization", "name": e["venue"].split(",")[0], "url": e["url"]},
        "offers": offer,
    }
    body = f"""
<section class="event-hero"><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/#directory">NYE events</a> › {escape(e['name'])}</nav>
<span class="eyebrow">New Year's Eve {Y} · {escape(e['suburb'])}</span>
<h1 style="font-size:clamp(2rem,5vw,3.4rem)">{escape(e['name'])}</h1>
<p class="lead muted" style="font-size:1.15rem;max-width:760px">{escape(e['blurb'])}</p>
</div></section>
<section style="padding-top:10px"><div class="wrap event-layout">
<div>
<div class="panel"><h2 style="font-size:1.5rem">What's included</h2><ul class="ticks">{inc}</ul></div>
<div class="prose" style="margin-top:30px">
<h2 style="font-size:1.5rem">About {escape(e['name'])}</h2>
<p>{escape(e['name'])} is at {escape(e['venue'])} in {escape(e['suburb'])} ({escape(e['area'])}). It's one of the {escape(cats.lower())} options for New Year's Eve {Y} in Melbourne. Fireworks: <b>{escape(e['fireworks'])}</b>. Age: <b>{escape(e['age'])}</b>.</p>
<p>Planning the rest of your night? Check the <a href="/plan-your-night/">fireworks timeline and transport tips</a> or compare <a href="/melbourne-fireworks-vantage-points/">fireworks vantage points around Melbourne</a>.</p>
<p class="notice">Details are based on the venue's published NYE information and can change. Confirm the price, times and inclusions with {escape(e['venue'].split(',')[0])} before booking. Are you the venue? <a href="/list-your-event/">Claim and upgrade this listing</a>.</p>
</div></div>
<aside class="side panel">
<div class="price" style="font-size:2rem">{"Free" if e['price_from']==0 else money(e['price_from']) if e['price_from'] else "TBA"}<small>{escape(e['price_text'])}</small></div>
<dl><dt>Date</dt><dd>Thursday 31 December {Y}</dd><dt>Time</dt><dd>{escape(e['time'])}</dd>
<dt>Where</dt><dd>{escape(e['venue'])}</dd><dt>Fireworks</dt><dd>🎆 {escape(e['fireworks'])}</dd><dt>Age</dt><dd>{escape(e['age'])}</dd></dl>
<a class="btn btn-primary" style="width:100%;justify-content:center" href="{e['url']}" target="_blank" rel="noopener sponsored">Book with the venue →</a>
<div style="margin-top:20px">{countdown(mini=True)}</div>
</aside>
</div></section>
<section class="alt"><div class="wrap"><div class="section-head"><h2>You might also like</h2></div>
<div class="grid">{''.join(card(x, i) for i, x in enumerate(related))}</div></div></section>
{list_band()}"""
    return layout(
        path,
        (f"{e['name']} {Y}" if "NYE" in e["name"] or "New Year" in e["name"] else f"{e['name']} NYE {Y}")
        + f" – {e['suburb']} | NYE in Melbourne",
        f"{e['name']} New Year's Eve {Y} in {e['suburb']}: {e['price_text']}. {e['blurb']}"[:300],
        body, og_type="article", active="/#directory",
        schema=[schema, breadcrumbs(("Home", "/"), ("NYE events", "/#directory"), (e["name"], path))],
    )


def page_vantage():
    vp = [e for e in EVENTS if "vantage" in e["categories"]]
    faq = FAQ[1:3] + FAQ[5:6] + FAQ[7:8]
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">NYE {Y} · Free &amp; ticketed</span>
<h1>Melbourne fireworks vantage points {Y}</h1>
<p class="lead">Where to watch the Melbourne New Year's Eve fireworks: the official Celebration Zones, riverside spots in the city, and hills, parks and beaches with skyline views. Includes the alcohol rules for each.</p></div></section>
<section><div class="wrap">
<div class="section-head"><h2>Vantage points at a glance</h2><p>Celebration Zones and closures are set by the City of Melbourne each year, and other councils set their own rules. The 2026 zones had not been announced at the time of writing, so check official updates before you go.</p></div>
{vantage_table()}
</div></section>
{directory(vp, "Free zones and guaranteed spots", "The official Celebration Zones need no booking. For a guaranteed view from above, the Skydeck sells tickets for a party on level 88.", show_filters=False)}
<section class="alt"><div class="wrap prose">
<h2>How to choose a vantage point</h2>
<p><b>For entertainment and facilities</b>, pick one of the official Celebration Zones. In 2025 they were Docklands, Kings Domain, Treasury Gardens and Flagstaff Gardens, with DJs, food trucks and accessible toilets from 6pm.</p>
<p><b>To be on the river</b>, try Federation Square, Birrarung Marr or the Southbank Promenade. These are the busiest spots in the city, and bridges and streets around them close to pedestrians as the night goes on.</p>
<p><b>For space and a quieter night</b>, head out of the CBD. The midnight fireworks launch from rooftops across the skyline, so Ruckers Hill in Northcote, Edinburgh Gardens, St Kilda foreshore and Williamstown all give a wide view of the city.</p>
<p><b>With kids</b>, make the 9:30pm fireworks your main event. The Celebration Zones and Footscray Park are alcohol-free and family-focused.</p>
<h2>What to bring</h2>
<ul><li>Picnic rug and low chair</li><li>Water, snacks, a hat and sunscreen</li><li>An umbrella or light jacket: the event goes ahead rain or shine</li><li>Charged phone and a power bank</li><li>No alcohol at the official event, and no glass on the St Kilda foreshore</li></ul>
</div></section>
<section id="faq"><div class="wrap"><div class="section-head"><h2>Vantage point FAQ</h2></div><div class="faq">{faq_html(faq)}</div></div></section>
{list_band()}"""
    return layout(
        "/melbourne-fireworks-vantage-points/",
        f"Melbourne Fireworks New Year's Eve {Y}: Best Free Vantage Points | NYE in Melbourne",
        f"The best places to watch the Melbourne New Year's Eve fireworks in {Y}: free Celebration Zones, riverside spots, Ruckers Hill, St Kilda and Williamstown, plus alcohol rules and when to arrive.",
        body, schema=[faq_schema(faq), item_list(vp, "Melbourne NYE vantage points"),
                      breadcrumbs(("Home", "/"), ("Vantage points", "/melbourne-fireworks-vantage-points/"))],
    )


def page_plan():
    faq = [FAQ[0], FAQ[6], FAQ[7], FAQ[8]]
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">Planning guide</span>
<h1>Plan your Melbourne NYE {Y}</h1>
<p class="lead">Fireworks times, the run sheet for the night, free public transport, road and bridge closures, accessibility and what to bring.</p>
{countdown(mini=True)}</div></section>
<section><div class="wrap two" style="align-items:start">
<div><h2>Fireworks times &amp; the night's schedule</h2><p class="muted">Times and closures are based on the 2025 event. The City of Melbourne publishes the final {Y} program at nye.melbourne.vic.gov.au closer to the night.</p></div>
{timeline_html()}
</div></section>
<section class="alt" id="transport"><div class="wrap prose">
<h2>Getting there: free public transport</h2>
<p>Public transport is the best way in and out of the city on New Year's Eve. In 2025, all Victorian public transport was free from 6pm on 31 December until 6am on 1 January, so you didn't need to touch on with a myki. Hundreds of extra trains, trams and buses ran through the night, with trains every 10–20 minutes in the evening and after midnight.</p>
<ul><li>Plan your trip on <a href="https://www.ptv.vic.gov.au" rel="noopener" target="_blank">ptv.vic.gov.au</a> and check the special NYE timetable.</li>
<li>In 2025, Flinders Street and Southern Cross stations stayed open all night, and Parliament, Flagstaff and Melbourne Central were open until 3am. The new Metro Tunnel stations closed from 7pm.</li>
<li>Many CBD tram stops close from mid-afternoon. Allow extra time and have a back-up station in mind.</li>
<li>After midnight, expect queues. Wait for the first wave to clear before heading for the station.</li></ul>
<h2 id="roads">Road and bridge closures</h2>
<p>In 2025, CBD road closures began around 4pm, with restricted access to the Docklands Victoria Harbour Promenade. From 7pm the Northbank and Southbank pedestrian bridges and Sandridge Bridge closed, and from 10:30pm Swanston Street between Hamer Hall and Collins Street (including Princes Bridge) and Flinders Street between Elizabeth and Russell Streets closed to pedestrians. Taxis and rideshare are hard to find near the city, so if you have to drive, park well outside the CBD and finish by public transport.</p>
<h2 id="alcohol">Alcohol rules</h2>
<p>The City of Melbourne's New Year's Eve is an alcohol-free event and fines apply, including in every Celebration Zone. Other councils set their own rules: Footscray Park's event is alcohol-free, Hobsons Bay has alcohol-free zones in Williamstown, and glass is banned on the St Kilda foreshore. For a drink with a view, book a licensed venue, party or <a href="/new-years-eve-cruises-melbourne/">NYE cruise</a>.</p>
<h2 id="accessibility">Accessibility</h2>
<p>In 2025 all Celebration Zones were accessible and had accessible toilets, though the grassy, sloping ground at Flagstaff Gardens, Treasury Gardens and Kings Domain can be harder to get around. Registered service animals are allowed (fireworks noise can affect them), and staff are trained to help people wearing the Hidden Disabilities Sunflower. Many venues in our directory have step-free access. Contact the venue to confirm.</p>
<h2>Safety &amp; wellbeing</h2>
<ul><li>Drink plenty of water. It can be a hot day and a long night.</li><li>Agree on a meeting point with your group.</li><li>Expect a large police presence. In 2025 the CBD and St Kilda foreshore were designated search areas.</li><li>Follow police and staff directions, and look after your mates.</li></ul>
</div></section>
<section id="faq"><div class="wrap"><div class="section-head"><h2>Planning FAQ</h2></div><div class="faq">{faq_html(faq)}</div></div></section>
{list_band()}"""
    return layout(
        "/plan-your-night/",
        f"Melbourne NYE {Y} Fireworks Times, Free Transport & Road Closures | NYE in Melbourne",
        f"Melbourne New Year's Eve {Y} planning guide: 9:30pm and midnight fireworks times, the schedule for the night, free public transport, road and bridge closures, alcohol rules and accessibility.",
        body, schema=[faq_schema(faq), breadcrumbs(("Home", "/"), ("Plan your night", "/plan-your-night/"))],
    )


def page_list():
    p = CONFIG["listing_price"]
    has_pay = "YOUR_" not in CONFIG["payment_link"]
    form_sub = (f"Fill this in, then pay ${p} securely. We'll publish your page and email you the link." if has_pay
                else f"Fill this in and we'll email you a ${p} invoice within one business day. Your page goes live once it's paid.")
    submit_label = f"Continue to payment: ${p} →" if has_pay else "Send my listing request →"
    cats = "".join(f'<option value="{k}">{v}</option>' for k, v in CATEGORY_LABELS.items() if k not in ("budget", "free"))
    faq = [
        ("What do I get for $" + str(p) + "?", "A dedicated event page built for search, with Google Event structured data. You also get a listing in our main directory and the matching category pages (dinners, cruises, parties, family), a direct link to your own booking page, and edits until 31 December."),
        ("Why should I list now rather than in December?", "Search interest in Melbourne New Year's Eve builds from October and peaks in the final weeks of December. Listing early means your page is live and indexed by Google for the whole season, not just the last-minute rush. New pages can take days or weeks to rank, so the earlier you're in, the more of the season you capture. It's the same $" + str(p) + " whenever you list."),
        ("Do you take commission on bookings?", "No. Guests book directly with you through your own link, and you keep 100% of every ticket."),
        ("How long does my listing stay live?", f"Your listing stays live until New Year's Day {NY}, then rolls into our archive. Previous listers get first right to renew for next year."),
        ("How fast will my listing go live?", "Usually within one business day of payment. We'll email you the link."),
        ("Can I update prices or details?", "Yes. Email us any changes (sold-out tiers, price releases, new acts) and we'll update your page."),
    ]
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">For venues, promoters &amp; cruise operators</span>
<h1>List your New Year's Eve event</h1>
<p class="lead">October, November and December are when Melbourne searches for its New Year's Eve plans. Put your NYE {Y} event in front of people typing "NYE in Melbourne", "New Year's Eve Melbourne", "NYE dinner Melbourne" and "New Year's Eve cruise Melbourne" while they're choosing where to spend the night.</p>
{countdown(mini=True)}
<p class="cd-note" style="margin-top:0">left to sell. The NYE search season is on now.</p>
<div class="cta-row"><a class="btn btn-primary" href="#form">List my event: ${p}</a><a class="btn btn-ghost" href="#season">Why now?</a></div></div></section>
{season_section(p)}
<section><div class="wrap two" style="align-items:start">
<div>
<h2>Why list with <span class="grad">NYE in Melbourne</span>?</h2>
<ul class="ticks">
<li><b>High-intent visitors.</b> People only visit a NYE guide when they're about to book.</li>
<li><b>Your own SEO page.</b> Each event gets a dedicated page with Google Event schema, which can make it eligible for event rich results.</li>
<li><b>Listed where people browse.</b> You appear in the main directory plus every matching category: dinners, cruises, parties and family.</li>
<li><b>Zero commission.</b> Guests click straight through to your booking page.</li>
<li><b>Updates until NYE.</b> Change prices, add tiers or mark sold-out tiers whenever you like.</li>
<li><b>Our name is the search.</b> NYE in Melbourne is built around the exact phrases people type into Google, so every page targets them.</li>
<li><b>Countdown traffic.</b> Interest builds from October and peaks in December, right when you're selling.</li>
</ul>
</div>
<div class="pricing">
<span class="eyebrow">NYE {Y} listing</span>
<div class="amount"><sup>$</sup>{p}</div>
<p class="muted">AUD inc GST · one-off · no commission</p>
<ul class="ticks">
<li>Dedicated event page + Google Event schema</li>
<li>Directory &amp; category page placement</li>
<li>Direct "Book" button to your site</li>
<li>Unlimited edits until 31 Dec {Y}</li>
<li>Live within 1 business day</li>
</ul>
<a class="btn btn-primary" href="#form" style="width:100%;justify-content:center">List my event →</a>
</div>
</div></section>
<section class="alt" id="form"><div class="wrap" style="max-width:860px">
<div class="section-head"><h2>Your event details</h2><p>{form_sub}</p></div>
<form class="listing panel" data-endpoint="{CONFIG['form_endpoint']}" data-payment="{CONFIG['payment_link']}" data-email="{CONFIG['contact_email']}">
<div><label for="f-name">Event name *</label><input id="f-name" name="event_name" required></div>
<div><label for="f-venue">Venue *</label><input id="f-venue" name="venue" required></div>
<div><label for="f-suburb">Suburb *</label><input id="f-suburb" name="suburb" required></div>
<div><label for="f-cat">Type *</label><select id="f-cat" name="category" required>{cats}</select></div>
<div><label for="f-price">Price from (AUD pp)</label><input id="f-price" name="price_from" inputmode="decimal" placeholder="e.g. 249"></div>
<div><label for="f-time">Times</label><input id="f-time" name="times" placeholder="e.g. 7pm – 1am"></div>
<div><label for="f-fw">Fireworks view</label><select id="f-fw" name="fireworks"><option>Both 9:30pm &amp; midnight</option><option>Midnight only</option><option>9:30pm only</option><option>Skyline / distant view</option><option>No view</option></select></div>
<div><label for="f-age">Age</label><select id="f-age" name="age"><option>18+</option><option>All ages</option><option>Family-friendly</option></select></div>
<div class="full"><label for="f-url">Booking URL *</label><input id="f-url" name="booking_url" type="url" required placeholder="https://"></div>
<div class="full"><label for="f-desc">Description &amp; inclusions *</label><textarea id="f-desc" name="description" required placeholder="What makes your night special? Food, drinks, DJs, views…"></textarea></div>
<div><label for="f-contact">Contact name *</label><input id="f-contact" name="contact_name" required></div>
<div><label for="f-email">Email *</label><input id="f-email" name="email" type="email" required></div>
<div><label for="f-phone">Phone</label><input id="f-phone" name="phone" type="tel"></div>
<div><label for="f-abn">Business / ABN</label><input id="f-abn" name="business"></div>
<input type="hidden" name="_subject" value="New NYE in Melbourne listing request (${p})">
<input type="hidden" name="_template" value="table"><input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">
<div class="full"><button class="btn btn-primary" type="submit">{submit_label}</button>
<p class="form-status muted" aria-live="polite" style="margin:12px 0 0"></p></div>
</form>
</div></section>
<section><div class="wrap"><div class="section-head"><h2>Listing FAQ</h2></div><div class="faq">{faq_html(faq)}</div></div></section>"""
    service = {
        "@context": "https://schema.org", "@type": "Service", "name": f"NYE {Y} event listing",
        "provider": {"@type": "Organization", "name": CONFIG["site_name"], "url": URL + "/"},
        "areaServed": "Melbourne, VIC",
        "offers": {"@type": "Offer", "price": p, "priceCurrency": "AUD", "url": URL + "/list-your-event/"},
    }
    return layout(
        "/list-your-event/",
        f"List Your New Year's Eve Event in Melbourne – ${p} | NYE in Melbourne",
        f"Promote your Melbourne New Year's Eve {Y} party, dinner or cruise. ${p} flat fee, no commission: a dedicated SEO event page, directory placement and a direct booking link.",
        body, schema=[service, faq_schema(faq), breadcrumbs(("Home", "/"), ("List your event", "/list-your-event/"))],
    )


def page_404():
    body = f"""<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}<div class="wrap">
<h1>This page fizzled out</h1><p class="lead">The page you're after isn't here, but the fireworks still are.</p>{countdown()}
<div class="cta-row"><a class="btn btn-primary" href="/">Back to all NYE events</a></div></div></section>"""
    return layout("/404.html", "Page not found | NYE in Melbourne", "Page not found.", body).replace(
        'content="index,follow', 'content="noindex,follow')


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#07061a"/><g stroke-linecap="round" stroke-width="4"><path d="M32 32 32 8" stroke="#ffc94d"/><path d="M32 32 53 20" stroke="#ff4fa3"/><path d="M32 32 53 44" stroke="#8b5cff"/><path d="M32 32 32 56" stroke="#41e3ff"/><path d="M32 32 11 44" stroke="#ffc94d"/><path d="M32 32 11 20" stroke="#ff4fa3"/></g><circle cx="32" cy="32" r="5" fill="#fff"/></svg>"""

OG_HTML = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;700&family=Playfair+Display:wght@800&display=swap" rel="stylesheet">
<style>body{{margin:0;width:1200px;height:630px;background:radial-gradient(ellipse at 50% 120%,#2a1a6b,transparent 60%),radial-gradient(ellipse at 85% 0%,#3a0f4d,transparent 55%),#07061a;color:#fff;font-family:Inter,sans-serif;position:relative;overflow:hidden}}
.t{{position:absolute;left:70px;top:90px;right:70px}}h1{{font-family:'Playfair Display',serif;font-size:96px;margin:0;line-height:1}}
.g{{background:linear-gradient(120deg,#ffc94d,#ff4fa3 50%,#8b5cff);-webkit-background-clip:text;color:transparent}}
p{{font-size:34px;color:#cfc9ff;margin:24px 0 0}}.b{{display:inline-block;margin-top:30px;padding:12px 26px;border-radius:99px;background:linear-gradient(120deg,#ffc94d,#ff4fa3);color:#14062b;font-weight:700;font-size:26px}}
.s{{position:absolute;bottom:0;left:0;width:100%}}.dot{{position:absolute;border-radius:50%}}</style></head><body>
<div class="t"><h1>NYE <span class="g">in Melbourne</span></h1><p>Fireworks · Cruises · Dinners · Parties<br>New Year's Eve {Y} in Melbourne</p><span class="b">Countdown to {NY} →</span></div>
{SKYLINE.replace('class="skyline"', 'class="s"')}
<script>for(let k=0;k<4;k++){{const cx=790+k*110,cy=250+(k%2)*95,c=['#ffc94d','#ff4fa3','#8b5cff','#41e3ff'][k];for(let i=0;i<48;i++){{const a=i/48*6.283,r=30+Math.random()*40,d=document.createElement('div');d.className='dot';d.style.cssText=`left:${{cx+Math.cos(a)*r}}px;top:${{cy+Math.sin(a)*r}}px;width:4px;height:4px;background:${{c}};box-shadow:0 0 8px ${{c}}`;document.body.appendChild(d)}}}}</script>
</body></html>"""


def build():
    if OUT.exists():
        og_keep = (OUT / "og.png").read_bytes() if (OUT / "og.png").exists() else None
        shutil.rmtree(OUT)
    else:
        og_keep = None
    OUT.mkdir()
    pages = {"/": page_home(), "/melbourne-fireworks-vantage-points/": page_vantage(),
             "/plan-your-night/": page_plan(), "/list-your-event/": page_list()}
    for c in CATEGORY_PAGES:
        pages[c["path"]] = page_category(c)
    for e in EVENTS:
        pages[f"/events/{e['slug']}/"] = page_event(e)
    for path, html in pages.items():
        f = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html)
    (OUT / "404.html").write_text(page_404())
    shutil.copy(ROOT / "src" / "style.css", OUT / "style.css")
    shutil.copy(ROOT / "src" / "main.js", OUT / "main.js")
    (OUT / "favicon.svg").write_text(FAVICON)
    (OUT / "og.html").write_text(OG_HTML)
    if og_keep:
        (OUT / "og.png").write_bytes(og_keep)
    (OUT / ".nojekyll").write_text("")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /og.html\n\nSitemap: {URL}/sitemap.xml\n")
    prio = lambda p: "1.0" if p == "/" else "0.6" if p.startswith("/events/") else "0.8"
    sm = "".join(
        f"<url><loc>{URL}{p}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{prio(p)}</priority></url>\n"
        for p in pages
    )
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}</urlset>\n')
    print(f"Built {len(pages)} pages into {OUT}")


if __name__ == "__main__":
    build()

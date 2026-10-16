# Cursed Router

> **Scope & authorization — read first.**
> Cursed Router is a local-only, lab-network novelty project built for a "useless projects"
> hackathon. It is a theatrical prank appliance, **not** a surveillance or attack tool.
>
> **Authorized use:** only on networks and hardware you own or are explicitly permitted to
> test on, with the knowing participation of the people connecting to it.
>
> **Hard boundaries this project commits to:**
> - **No credential capture.** It never collects, stores, or transmits passwords, form input,
>   cookies, tokens, or any secret a client enters on an intercepted page.
> - **No real-user data retention.** Telemetry logs local prank events (modes toggled, pages
>   mutated) — not the contents of anyone's browsing.
> - **No exfiltration.** Nothing intercepted leaves the local machine.
> - **Visible, consensual theater.** Interventions (banners, redirects, silly portals) are meant
>   to be obvious and funny, not deceptive for gain.
>
> **Do not** deploy on shared, public, corporate, or otherwise unauthorized Wi-Fi, and do not
> use it to intercept traffic from people who have not agreed to the bit. The man-in-the-middle
> and captive-portal techniques here are the same primitives used by real attacks — keeping to
> the boundaries above is what makes this a prank instead of an intrusion.

A chaotic, modular Wi-Fi access point project for a useless-hackathon build: a router that behaves less like a network device and more like a prank-powered appliance. The goal is not to take over the internet; the goal is to turn a normal hotspot into a delightfully absurd, story-driven local network experience using hostapd as the access point and a collection of modules for captive portals, traffic weirdness, and manual client trolling.

This project is intentionally silly, experimental, and built for local-only lab environments. It is meant to be a creative engineering exercise: "what if your router had personality?"

---

## Why this exists

Because every serious networking project deserves a little chaos.

The Cursed Router is a playground for:

- building a modular hotspot stack around hostapd
- experimenting with Wi-Fi policy, client auth, and local routing
- exploring captive portal flows and browser redirection behavior
- creating harmless but absurd web “interventions” for local-only demo networks
- giving an admin panel a weirdly dramatic amount of power over connected clients

It is for hackathons, demos, and local experiments. It is not for production deployments or real-world public Wi-Fi.

---

## Core idea

A standard Wi-Fi hotspot is turned into a weird little control plane:

- hostapd creates the wireless network
- a local DHCP/DNS layer handles guest traffic
- a captive portal intercepts browser sessions
- a rule engine decides whether traffic should be redirected, transformed, or simply mocked
- an admin dashboard lets a human troll clients in real time

The result is a router that feels like it has opinions.

---

## High-level architecture

```text
                              +-----------------------+
                              |  Clients / Laptops    |
                              |  Phones / Tablets     |
                              +-----------+-----------+
                                          |
                                          v
                              +-----------------------+
                              |   hostapd hotspot     |
                              |   (Wi-Fi AP)          |
                              +-----------+-----------+
                                          |
                                          v
                              +-----------------------+
                              |  Network Control      |
                              |  DHCP / DNS / NAT     |
                              +-----------+-----------+
                                          |
                                          v
          +---------------------------+-------------------------------+
          |                                                           |
          v                                                           v
+----------------------+             +-------------------------------+
| Captive Portal Layer |             | Traffic Handling / MITM       |
| - splash page        |             | - DNS hijack                 |
| - auth state        |             | - redirect rules             |
| - magic QR codes    |             | - content rewriting          |
| - challenge flows    |             | - random page mutations      |
+----------+-----------+             +---------------+---------------+
           |                                             |
           v                                             v
+----------------------+             +-------------------------------+
| Auth / Policy Layer |             | Rule Engine / Admin Panel     |
| - allowlist / block |             | - per-client interventions   |
| - PPSK-like modes   |             | - manual override commands    |
| - magic passwords  |             | - event log / telemetry       |
+----------+-----------+             +-------------------------------+
           |                                             |
           +---------------------+---------------------------+
                                 v
                    +---------------------------+
                    | Telemetry + Logging       |
                    | - client events           |
                    | - portal logs             |
                    | - redirect history        |
                    +---------------------------+
```

---

## Modular architecture

The project is built around small, replaceable components. The idea is to keep each module focused and easy to mock/test in isolation.

### 1. Wi-Fi Layer

Responsible for creating the access point.

- hostapd configuration module
- SSID / channel management
- security modes and optional challenge flows
- per-network profiles (guest, cursed, admin, etc.)

Suggested roles:

- `wifi_ap`
- `ssid_manager`
- `interface_manager`

### 2. Auth Layer

Handles who is allowed to connect and under what rules.

Possible modes:

- normal WPA2/WPA3
- “magic password” mode for themed login flows
- PPSK-like experiment for local-only testing
- invite-only mode for curated demo sessions

Example playful modes:

- `magic-passwords`: the Wi-Fi password is accepted only when a client types a secret phrase like `banana-taxicab`
- `everyone-is-allowed`: local-only toy mode for a lab network where every password is accepted for testing
- `banhammer`: a manual per-client access toggle from the admin panel

### 3. DHCP / DNS / NAT Layer

This is where the router becomes “interesting.”

- local DHCP allocation
- DNS capture / override
- port forwarding and NAT management
- captive portal redirect plumbing

This layer is the backbone for making clients think they are on a normal network while the router quietly hijacks their browsing experience.

### 4. Captive Portal Layer

The “front door” to the cursed experience.

Features could include:

- fake login splash screens
- progressive “acceptable use” checkboxes
- themed branded pages such as “The Internet Has Been Temporarily Reinterpreted”
- social engineering style weirdness without going too far into malice

This module should be highly themeable and allow different portal experiences by network, time, or client group.

### 5. Traffic Intercept / MITM Layer

This is the part that makes pages look wrong in delightful ways.

Potential behaviors:

- redirect requests to a purposely silly local site
- replace page titles with absurd alternatives
- inject tiny CSS/JS pranks into visited pages
- subtle noise overlays or floating “do not trust this router” banners
- random “mood-of-the-hour” content mutations

Keep it local-only, debug-friendly, and obviously themed.

### 6. Rule Engine

A central policy engine that decides what weirdness to apply.

Examples:

- if client is on `device-7`, show a cat-themed portal
- if request is to `google.com`, redirect to a “not actually Google” page
- if current time is after 2am, inject sleepy-mode UI themes
- if a client enters a magic code, unleash a special prank mode

This module should be simple and declarative, ideally something like a list of rules or YAML-driven behaviors.

### 7. Admin Panel

The human-driven troll interface.

Possible controls:

- view connected clients
- disconnect a single device
- auto-redirect a client to a chosen page
- force a “fake browser update” splash screen
- toggle “everyone sees a cat banner” mode
- open the “this page is now run by a toaster” mode

This panel should feel like a tiny evil control room for local chaos.

### 8. Telemetry / Logging

Everything should be observable.

- client joins / disconnects
- portal login attempts
- redirect logs
- injected content summary
- admin actions
- weirdness metrics: “number of pages replaced today”

This makes the project feel like a real system rather than a pile of hacks.

---

## Fun cursed features

This is the part that makes the project feel like a hackathon winner.

### 1. The `internet is fine` redirect

Any uncaught DNS request routes to a local page that says:

- “The internet is fine.”
- “This is a completely normal browsing experience.”
- “The router has not become sentient.”

### 2. The page mutation engine

On certain domains, pages gain harmless but unnerving changes:

- title becomes “Actually this is a toaster”
- every heading is prefixed with a cat emoji
- navigation links say `Click here to continue being very calm`
- the favicon becomes a tiny spinning potato

### 3. Magic passwords

A user connects to the Wi-Fi and the router responds with prompts such as:

- `quasar-biscuit`
- `magic-toast`
- `weirdly-comfortable`
- `tiny-sorcerer`

Each password triggers a different “mood mode.”

Examples:

- `banana`: all websites become banana-themed
- `echo`: only certain pages are mirrored
- `shimmer`: pages receive a soft, spooky haze overlay
- `penguin`: web pages are renamed to penguin-themed editions

### 4. The “one device only” troll mode

A single client can be selected and then manually harassed:

- redirect all traffic to a fake “update required” page
- apply a weird CSS theme to only that client
- force splash-page loops until they submit a nonsense acceptance form
- show a fake system warning that says the router is updating the user’s ego

### 5. Captive portal with personality

Instead of a boring login page, the portal can be:

- comedic and impossible to take seriously
- generated in a style of an old 90s login system
- “officially” written by the router itself
- a fake “IT notice” that claims all traffic is being optimized for silliness

### 6. The cursed DNS map

Common domains become absurd local placeholders:

- `google.com` → very-legal-search.example
- `github.com` → the-future-of-coding.example
- `youtube.com` → this-is-not-a-video.example

It’s still a local demo network, so the effect is intentionally theatrical.

### 7. The local “admin voice” mode

A fake admin console that says things like:

- “We are experiencing a minor emotional event.”
- “Client 7 has entered clown mode.”
- “This network is now performing interpretive dancing.”

This is more fun than useful, and that is the point.

---

## Suggested project layout

```text
cursed-router/
├── README.md
├── app/
│   ├── main.py
│   ├── cli.py
│   └── config.py
├── modules/
│   ├── wifi/
│   │   ├── hostapd_manager.py
│   │   ├── ssid_profiles.py
│   │   └── client_state.py
│   ├── auth/
│   │   ├── auth_manager.py
│   │   ├── magic_passwords.py
│   │   └── ppsk_experiments.py
│   ├── portal/
│   │   ├── portal_server.py
│   │   ├── templates/
│   │   └── rules.py
│   ├── traffic/
│   │   ├── dns_overrides.py
│   │   ├── redirect_rules.py
│   │   ├── mitm_proxy.py
│   │   └── page_mutator.py
│   ├── admin/
│   │   ├── dashboard.py
│   │   └── client_actions.py
│   └── telemetry/
│       ├── logger.py
│       ├── events.py
│       └── metrics.py
├── rules/
│   ├── default.yaml
│   └── themes.yaml
├── assets/
│   ├── branding/
│   ├── css/
│   └── logos/
├── tests/
│   ├── test_auth.py
│   ├── test_rules.py
│   └── test_router_flow.py
├── scripts/
│   ├── start_router.sh
│   ├── stop_router.sh
│   └── deploy_hostapd.sh
├── requirements.txt
├── docker-compose.yml
└── Makefile
```

---

## Implementation principles

To keep the project fun and maintainable, the architecture should follow a few rules:

- small modules over giant monoliths
- config-driven behaviors over hardcoded logic
- local-only design; no public deployment
- clear separation between AP, auth, portal, and traffic paths
- “theme” abstraction so a new curse can be added without rewriting the router
- admin actions should be explicit and logged

A good project motto:

> The router should be silly, but the architecture should be clean.

---

## Suggested phases

### Phase 1: Basic hotspot

- install and configure hostapd
- create a test SSID
- confirm clients can join and receive DHCP

### Phase 2: Captive portal

- build a splash/login flow
- show a fake “internet access request” page
- log client sessions

### Phase 3: DNS and redirect rules

- intercept selected domains
- redirect clients to local prank pages
- make rules configurable and themeable

### Phase 4: Content mutation

- inject custom CSS/JS into visible pages
- randomize UI changes by client or time
- create a “mood mode” system

### Phase 5: Admin panel + client trolling

- manual client controls
- per-client rules
- event history and user actions

### Phase 6: Full cursed mode

- combine portal, DNS, and page mutation into a single themed experience
- ship a set of absurd but stable “modes”
- make the router “feel alive”

---

## Ethical / safety note

This project should be used only on networks you own or explicitly control for testing, demos, or learning. It is intentionally a local lab experiment for understanding how captive portals, AP policy, and traffic interception work in a controlled environment.

Do not deploy it on shared, public, or unauthorized wireless networks. The goal here is playful local experimentation, not malicious behavior.

---

## Hackathon pitch

“Cursed Router is a modular Wi-Fi hotspot that turns your local network into a tiny, theatrical world of absurd redirects, captive-portalled nonsense, and interactive trolling. Powered by hostapd and built with a clean rule-driven architecture, the project lets you play with Wi-Fi policy, browser hijacks, and admin-level chaos in a controlled, comedic environment.”

---

## Project vibes

This project is best described as:

- a local networking lab
- a UI/UX prank engine
- a weird admin dashboard
- a hostile but harmless internet mood ring
- a crash course in captive portals and packet flow without taking it too seriously

It should be fun, modular, and unmistakably cursed.

---

## Final thought

The most important thing is not whether the router “works” like a normal router. The important thing is whether it feels like a router that has a sense of humor.

If the admin panel can troll a client, the portal can be a theatrical event, and the DNS layer can redirect a browser toward absurdity with style, then the project has succeeded.

Build it cleanly. Curse it creatively. Make it funny.

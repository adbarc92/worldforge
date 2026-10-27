--
-- PostgreSQL database dump
--

\restrict 96htZBq2dR4aVTJN6GzWpoU9OIcz3jAFqhQV99aUi0PqsiOoZJONAIsPMQQEL4z

-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: canon_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO canon_user;

--
-- Name: contradictions; Type: TABLE; Schema: public; Owner: canon_user
--

CREATE TABLE public.contradictions (
    id character varying(36) NOT NULL,
    project_id character varying(36) NOT NULL,
    chunk_a_id character varying(36) NOT NULL,
    chunk_b_id character varying(36) NOT NULL,
    document_a_id character varying(36),
    document_b_id character varying(36),
    document_a_title character varying(500) DEFAULT ''::character varying NOT NULL,
    document_b_title character varying(500) DEFAULT ''::character varying NOT NULL,
    chunk_a_text text NOT NULL,
    chunk_b_text text NOT NULL,
    explanation text NOT NULL,
    status character varying(50) DEFAULT 'open'::character varying NOT NULL,
    resolved_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    resolution_note text
);


ALTER TABLE public.contradictions OWNER TO canon_user;

--
-- Name: documents; Type: TABLE; Schema: public; Owner: canon_user
--

CREATE TABLE public.documents (
    id character varying(36) NOT NULL,
    title character varying(500) NOT NULL,
    file_path character varying(1000) NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    chunk_count integer DEFAULT 0 NOT NULL,
    error_message text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    project_id character varying(36) NOT NULL
);


ALTER TABLE public.documents OWNER TO canon_user;

--
-- Name: projects; Type: TABLE; Schema: public; Owner: canon_user
--

CREATE TABLE public.projects (
    id character varying(36) NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.projects OWNER TO canon_user;

--
-- Name: syntheses; Type: TABLE; Schema: public; Owner: canon_user
--

CREATE TABLE public.syntheses (
    id character varying(36) NOT NULL,
    project_id character varying(36) NOT NULL,
    title character varying(500) DEFAULT 'World Primer'::character varying NOT NULL,
    outline json,
    outline_approved boolean DEFAULT false NOT NULL,
    content text,
    status character varying(50) DEFAULT 'outline_pending'::character varying NOT NULL,
    error_message text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.syntheses OWNER TO canon_user;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: canon_user
--

COPY public.alembic_version (version_num) FROM stdin;
e5f6a7b8c9d0
\.


--
-- Data for Name: contradictions; Type: TABLE DATA; Schema: public; Owner: canon_user
--

COPY public.contradictions (id, project_id, chunk_a_id, chunk_b_id, document_a_id, document_b_id, document_a_title, document_b_title, chunk_a_text, chunk_b_text, explanation, status, resolved_at, created_at, updated_at, resolution_note) FROM stdin;
203b2803-69d4-419a-89bf-ee6d4916863d	20d78ea3-d7ae-4654-b866-c5e9a63d9dfe	cac1e3ab-60e7-4eca-bc88-cb2fa7f2197d	843d5f8a-5078-4958-a5bb-e1ef4cee02a9	a82f76e9-06a8-4b6f-a8e9-1dd5e40d4dc8	f6efb49d-e714-41c8-952e-e5640f7b5098	old_logs.md	history.md	# Excerpts from Archivist Marr's Recovered Logs\n\n**Log 4412-A, dated 2411.09.14.**\n\nSpent the afternoon cleaning up the metadata on the founding-era records. The official history lists Aegis's construction as complete in 2387, but the original commissioning manifests I pulled from the sealed archive clearly date to 2384. Three years' discrepancy. I can't tell yet whether this is a clerical error propagated through the official timeline or something deliberate.\n\nWhat I can say with confidence: the station's first crew rotation arrived in 2385, not 2388. The records are internally consistent — transport logs from the *Orestes*, personnel transfer orders, even receipts for the first water-reclamation cartridges all point to the earlier date. Whoever wrote the public history used a different set of numbers.\n\n---\n\n**Log 4412-C, dated 2411.10.02.**\n\nAsked XO Koval about the date discrepancy offhand over breakfast. She didn't meet my eyes. Said she'd "look into it" and changed the subject. That's the third time this week someone has done that when I've raised founding-era records. I'm going to stop asking.\n\nThe more concerning piece: the original crew manifest names Commander Alvarado's predecessor — someone called *Rett Vaskel* — as the station's first director. There is no Rett Vaskel in the public record. No entry in the Commonwealth personnel database. No trace in any publication I can find. Alvarado is listed as the founding director in every official source.\n\nI don't know what happened between 2384 and 2388, but something did, and it's been papered over thoroughly.	# A Brief History of Aegis Station\n\nAegis Station's construction was authorized by the Terran Commonwealth's Science Directorate in 2385, two years after the completion of the Lyran Treaty that ended the border skirmishes with the Hegemony. The treaty opened the outer systems to civilian research vessels, and Aegis was conceived as the primary waystation for the return leg of the Lyran expeditions.\n\nConstruction began at the Hestia shipyards in 2385 and was completed in 2387. The station was ferried to the Kepler-186 system by the deep-space tug *Orestes* and assembled on station across eleven months. First crew boarded in late 2388.\n\nFor its first thirteen years, Aegis served its intended function: a quiet refueling and resupply point for expeditions returning from Lyran space. The discovery of the Halion anomaly by probe drops in 2401 changed the station's character dramatically. Within six months, the Science Directorate had repurposed three of Aegis's laboratories for dedicated anomaly research, and within a year the crew had grown by 60%.\n\nCommander Yusef Alvarado held directorship from 2388 through 2409. He oversaw both the original waystation era and the early anomaly years. His successor, Commander Vale, was appointed following Alvarado's retirement. Under Vale's tenure, Commonwealth Defense has taken an increasingly visible role in station affairs.\n\nThe station has never experienced a fatal accident. It has experienced two major reactor scrams (2392 and 2407) and one station-wide power interruption (2405, traced to a faulty coupling in the central bus).	The passages contradict each other on multiple key facts: Passage A states Aegis construction was complete in 2384 with first crew arriving in 2385, while Passage B states construction began in 2385 and was completed in 2387 with first crew boarding in late 2388. Additionally, Passage A identifies Rett Vaskel as the station's first director, while Passage B states Commander Alvarado held directorship from 2388 and lists him as the founding director. These are mutually exclusive claims about the same historical events.	dismissed	2026-04-20 05:31:12.880627	2026-04-19 20:52:58.146401	2026-04-20 05:31:12.882619	\N
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: canon_user
--

COPY public.documents (id, title, file_path, status, chunk_count, error_message, created_at, updated_at, project_id) FROM stdin;
bd3d01dc-c686-4d9f-b9a9-6de0ece3f407	Cosmology.md	/app/uploads/2a48223a-3331-4154-ba2e-fc7700dfe8ff.md	completed	5	\N	2026-04-09 19:31:14.099859	2026-04-09 19:31:16.460809	cf3a37e1-0b63-4e94-a657-5aefdb134e62
4dc6dd01-33ea-4a84-8b56-8077a4824064	Devices.md	/app/uploads/4807f26d-aa20-4ef2-8a86-741fffe8101c.md	completed	2	\N	2026-04-09 19:31:19.134319	2026-04-09 19:31:19.740208	cf3a37e1-0b63-4e94-a657-5aefdb134e62
e33278b0-0bd2-45e2-a131-ad266da2920c	Factions.md	/app/uploads/aff2a73d-1577-4484-b2c0-99da13a72d47.md	completed	4	\N	2026-04-09 19:31:21.887669	2026-04-09 19:31:22.214595	cf3a37e1-0b63-4e94-a657-5aefdb134e62
f8361c82-9a26-4ab7-a963-52a34b4f1b44	Locations.md	/app/uploads/50082397-2536-49ae-9a43-ba4486fc2cd9.md	completed	7	\N	2026-04-09 19:31:25.918445	2026-04-09 19:31:26.671672	cf3a37e1-0b63-4e94-a657-5aefdb134e62
1fc1b413-6099-4ed2-b5c2-e0ef53c19050	station.md	/app/uploads/ed219ac7-6a75-44cc-895b-7f6fd85ec4d8.md	completed	1	\N	2026-04-19 20:52:49.843414	2026-04-19 20:52:50.202951	20d78ea3-d7ae-4654-b866-c5e9a63d9dfe
0a7ac03a-6be6-4657-858d-c282bd048f52	crew.md	/app/uploads/80871b61-78b5-4840-8d38-440443c43db0.md	completed	1	\N	2026-04-19 20:52:50.279052	2026-04-19 20:52:50.756681	20d78ea3-d7ae-4654-b866-c5e9a63d9dfe
8d4b15f4-772b-48ef-9d3c-396fd435622b	signal.txt	/app/uploads/36763025-d5f7-4c40-befd-5e723ea781d2.txt	completed	1	\N	2026-04-19 20:52:50.820438	2026-04-19 20:52:51.063128	20d78ea3-d7ae-4654-b866-c5e9a63d9dfe
f6efb49d-e714-41c8-952e-e5640f7b5098	history.md	/app/uploads/aa883933-d45d-4a8c-979f-768a5651bebe.md	completed	1	\N	2026-04-19 20:52:51.130845	2026-04-19 20:52:51.367629	20d78ea3-d7ae-4654-b866-c5e9a63d9dfe
c15718b2-fce7-4f4a-9786-e8df04e65d3f	tech_brief.pdf	/app/uploads/969c2963-d531-440b-8707-b05afe0fd60c.pdf	completed	1	\N	2026-04-19 20:52:51.439514	2026-04-19 20:52:51.938483	20d78ea3-d7ae-4654-b866-c5e9a63d9dfe
a82f76e9-06a8-4b6f-a8e9-1dd5e40d4dc8	old_logs.md	/app/uploads/9b6e4035-10bb-4100-bd07-7aae0825b28c.md	completed	1	\N	2026-04-19 20:52:52.004926	2026-04-19 20:52:52.292549	20d78ea3-d7ae-4654-b866-c5e9a63d9dfe
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: canon_user
--

COPY public.projects (id, name, description, created_at, updated_at) FROM stdin;
cf3a37e1-0b63-4e94-a657-5aefdb134e62	Test	\N	2026-04-09 19:30:43.856537	2026-04-09 19:30:43.856542
20d78ea3-d7ae-4654-b866-c5e9a63d9dfe	Aegis Station	A mystery in deep space. Research outpost studying an anomalous signal from a gas giant.	2026-04-19 20:52:49.762597	2026-04-19 20:52:49.762609
\.


--
-- Data for Name: syntheses; Type: TABLE DATA; Schema: public; Owner: canon_user
--

COPY public.syntheses (id, project_id, title, outline, outline_approved, content, status, error_message, created_at, updated_at) FROM stdin;
7b0cc900-714e-41e8-9902-2d0b55f63983	20d78ea3-d7ae-4654-b866-c5e9a63d9dfe	World Primer	[{"title": "Historical Overview", "description": "Timeline of major events, historical records, and documented discrepancies in the chronological record"}, {"title": "Government Structure and Classification", "description": "Political systems, administrative hierarchies, and information security protocols"}, {"title": "Space Infrastructure", "description": "Design, construction, and operational frameworks of orbital stations and space-based facilities"}, {"title": "Research Facilities and Operations", "description": "Scientific installations, research methodologies, and operational procedures for knowledge gathering"}, {"title": "Advanced Technology Systems", "description": "Reactor technology, power generation systems, and other critical technological infrastructure"}, {"title": "Electromagnetic Phenomena", "description": "Anomalous electromagnetic events, their properties, and their impact on technology and operations"}, {"title": "Personnel and Organization", "description": "Staffing structures, roles and responsibilities, and human resource management in space environments"}, {"title": "Scientific Research Programs", "description": "Ongoing research initiatives, experimental protocols, and knowledge advancement efforts"}, {"title": "Operational Protocols", "description": "Standard operating procedures, safety protocols, and day-to-day management of space-based operations"}]	t	# Historical Overview\n\nWhen the Terran Commonwealth first conceived Aegis Station in 2385, it was meant to be a simple waystation—a place for weary expedition crews to refuel and resupply on their long journey home from Lyran space. The border skirmishes with the Hegemony had finally ended with the Lyran Treaty two years prior, opening the outer systems to civilian research for the first time in decades. What the Commonwealth built was functional and unremarkable: a deep-space platform that could keep 214 souls alive in the void while they serviced the steady stream of returning exploration vessels.\n\nThe official records tell us that construction began at the Hestia shipyards in 2385, concluded in 2387, and that the first crew arrived in late 2388 under the leadership of Commander Yusef Alvarado. For thirteen quiet years, this version of events seemed sufficient. Aegis performed its intended role without fanfare, a reliable dot of light in the darkness between the outer systems and home.\n\nBut history, as any archivist will tell you, is rarely as clean as the official chronicles suggest. The founding years of Aegis Station are marked by curious inconsistencies—dates that don't align, names that appear in some records and vanish from others, and a troubling tendency for anyone who asks too many questions to be met with uncomfortable silences. The transport logs from the *Orestes*, the ship that ferried the station to its current position, tell a different story than the public histories. Personnel transfer orders, supply manifests, even mundane receipts for water-reclamation cartridges all point to events happening years earlier than officially recorded. Most puzzling of all, the original crew manifest names someone called Rett Vaskel as the station's first director—a person who, according to every accessible Commonwealth database, never existed.\n\nWhatever happened between 2384 and 2388 has been carefully erased, leaving only shadows and contradictions for those persistent enough to look. The discrepancies might have remained buried indefinitely if not for a discovery in 2401 that transformed Aegis from a forgotten waystation into something far more significant.\n\nThe Halion anomaly changed everything. When automated probes dropped into the gas giant's upper atmosphere detected the first pulse—a precise, recurring electromagnetic signal emerging from 40,000 kilometers below the cloud deck—the Commonwealth's Science Directorate moved swiftly. Within six months, three of Aegis's laboratories had been repurposed for dedicated anomaly research. Within a year, the crew had grown by sixty percent. The quiet refueling stop had become the epicenter of humanity's first potential contact with something genuinely alien.\n\nThe signal itself defies easy categorization. Every 47 hours, with clockwork precision, a pulse of electromagnetic energy emerges from somewhere deep within Halion and propagates outward in a perfect sphere. The transmission lasts exactly 3.7 seconds and occupies the hydrogen line—a frequency that any spacefaring civilization would immediately recognize as significant. Some researchers, led by Dr. Anika Rho, argue that the waveform contains deliberate structure, evidence of an intentional transmission rather than a natural phenomenon. Others, including Dr. Elias Fen, find no statistically significant patterns in the data. The debate has raged for over a decade, growing more heated as the Commonwealth Defense classification on the anomaly data was extended indefinitely in 2411.\n\nThe station itself has weathered the transformation from waystation to research facility with typical Commonwealth engineering resilience. Its three concentric rings—outer for life support and quarters, middle for laboratories and computing, inner for observation and archives—have housed a steady population of scientists, support staff, and an increasingly visible security contingent. The main fusion reactor has performed admirably, suffering only two automated shutdowns in its twenty-five-year service life. Both incidents were traced to sensor faults or equipment failures, though it's worth noting that the 2407 scram occurred just eleven seconds after a Halion pulse—a correlation that remains under investigation.\n\nCommander Alvarado oversaw both the original waystation era and the early years of anomaly research before retiring in 2409. His successor, Commander Iresh Vale, inherited a station that had grown far beyond its original mandate. Under her tenure, the research has intensified, the security presence has expanded, and the questions surrounding Aegis's founding years have taken on new urgency. In a facility dedicated to studying the unknown, the station's own mysterious origins serve as a constant reminder that some secrets resist even the most determined investigation.\n\nToday, Aegis Station orbits Halion with the patient persistence of a civilization waiting for answers. Every 47 hours, the pulse emerges from the depths below, briefly disrupting elevator systems and medical monitors before fading back into silence. The researchers continue their work, the archivists continue their careful excavation of buried records, and somewhere in the restricted files, the truth about those missing years waits to be discovered. Whether that truth will prove as significant as the anomaly itself remains to be seen.\n\n---\n\n# Government Structure and Classification\n\nWelcome to a world where power flows through carefully constructed hierarchies, where information is currency, and where the line between civilian research and military oversight grows thinner with each passing day.\n\nIn this universe, the Terran Commonwealth stands as the dominant political entity, a sprawling government that has expanded beyond Earth to claim dominion over multiple star systems. The Commonwealth operates through specialized directorates — the Science Directorate oversees research initiatives, while Commonwealth Defense handles military and security matters. This division of authority creates a complex web of competing interests, particularly evident in remote installations where civilian research intersects with potential security concerns.\n\nConsider Aegis Station, orbiting the gas giant Halion in the outer reaches of the Kepler-186 system. Here, the Commonwealth's administrative structure reveals itself in microcosm. Commander Iresh Vale holds the position of Station Director, wielding ultimate authority over the facility's 187 personnel. Below her, Executive Officer Maren Koval manages day-to-day operations with the efficiency of her thirty-year Navy background, while specialists like Chief Engineer Teodor Weiss maintain the critical systems that keep everyone alive in the void.\n\nYet even this seemingly straightforward hierarchy contains hidden complexities. Captain Drest Hollow, Head of Station Security, reports directly to Commander Vale — but he also maintains a private communications channel to Commonwealth Defense. This dual loyalty exemplifies how information security protocols permeate every level of operations. Knowledge is compartmentalized, access is restricted, and even civilian contractors like Archivist Teague Marr find themselves navigating carefully controlled information flows.\n\nThe station's research facilities demonstrate this layered approach to classification. While Aegis operates officially as a civilian research outpost, three of its laboratories function under Commonwealth Defense classifications. The existence of these labs is publicly acknowledged — their research emphatically is not. Dr. Anika Rho's controversial theories about the Halion anomaly, Dr. Elias Fen's computational xenology work, and whatever classified projects occupy those restricted laboratories all exist within carefully maintained security boundaries.\n\nThis information architecture extends even to historical records. Archivist Marr's discoveries reveal how the Commonwealth manages inconvenient truths — through selective editing of official histories, careful curation of accessible records, and the quiet disappearance of individuals like the mysterious Rett Vaskel from public documentation. The three-year discrepancy between actual construction dates and official histories suggests that information control begins at the very moment events occur.\n\nThe Commonwealth's approach to governance relies heavily on this compartmentalization of knowledge. Personnel operate within their designated spheres of access, reporting through established chains of command while remaining unaware of activities beyond their clearance levels. When XO Koval deflects Marr's questions about historical inconsistencies, when Commander Vale rarely leaves the command deck, when Commonwealth Defense extends classification periods indefinitely — these aren't isolated incidents but manifestations of a systematic approach to controlling information flow.\n\nThis creates a government structure that functions through managed ignorance as much as shared knowledge. Personnel perform their duties efficiently within their assigned parameters while remaining deliberately uninformed about the broader implications of their work. The system maintains stability through this careful balance of authority and opacity, ensuring that even in the depths of space, the Commonwealth's hierarchical control remains absolute.\n\nIn this world, understanding your place in the hierarchy means understanding not just what you're authorized to know, but what you're expected not to ask about. The smooth functioning of installations like Aegis Station depends on this unspoken agreement — that some questions remain unasked, some answers remain classified, and some truths remain buried in restricted archives accessible only to those with the proper clearance levels.\n\n---\n\n# Space Infrastructure\n\nWhen humanity first ventured beyond the inner systems, they discovered that space demanded a different kind of architecture—one built not just to shelter life, but to sustain it across the vast emptiness between worlds. The story of how we learned to build in the void is written in stations like Aegis, orbiting the gas giant Halion in the distant Kepler-186 system.\n\nAegis Station represents the pinnacle of what the Terran Commonwealth calls Class-IV deep-space platforms—massive structures designed to operate independently for decades without resupply. Picture three concentric rings connected by six radial spokes, each ring serving a carefully planned function. The outermost ring houses the crew quarters and life support systems, keeping 214 souls breathing in the vacuum. The middle ring contains the research laboratories and central computing core—the brain of the station. The innermost ring, closest to the fusion reactor's heart, holds observation decks and restricted archives where the most sensitive work takes place.\n\nThe genius of such designs lies not in their complexity, but in their self-sufficiency. Aegis produces 92% of its food through hydroponic bays, turning artificial sunlight and carefully recycled nutrients into sustenance. Water reclamation systems capture every drop of moisture from the station's atmosphere, achieving an efficiency rate of 99.3%—because in space, waste is not just inefficient, it's potentially fatal. The station's fusion reactor generates 1.8 terawatts of power continuously, with two backup reactors waiting in reserve, because the difference between light and darkness is measured in minutes when your nearest help is months away.\n\nBuilding such a station requires more than engineering—it demands a kind of industrial choreography. Aegis was constructed at the Hestia shipyards in the inner system, then ferried piece by piece to its destination by the deep-space tug *Orestes*. The assembly process took eleven months of careful work in the shadow of Halion, with crews working in environmental suits to connect massive structural elements while the gas giant's radiation belts flickered around them.\n\nWhat makes space infrastructure truly remarkable is its adaptability. Aegis was originally designed as a waystation—a place for ships returning from the Lyran expeditions to refuel and resupply. But when automated probes discovered something extraordinary in Halion's atmosphere in 2401—a recurring electromagnetic pulse emerging every 47 hours—the station transformed overnight. Laboratories were repurposed, crew expanded by sixty percent, and what had been a quiet stopover became a center for studying one of the most puzzling phenomena humanity had encountered.\n\nThe pulse itself occupies the hydrogen line at 1420 MHz, lasting exactly 3.7 seconds each time it emerges from 40,000 kilometers below Halion's cloud deck. Some researchers argue the signal shows signs of artificial structure, while others maintain it's a natural phenomenon. The debate rages in the station's laboratories while the pulse continues its precise rhythm, indifferent to human theories about its origin.\n\nThis adaptability extends to the human element as well. Space infrastructure succeeds or fails based on the people who operate it, and stations like Aegis develop their own cultures over decades of operation. Commander Iresh Vale, a former xenolinguist, has directed the station since 2409, overseeing both civilian research and the increasingly classified work that Commonwealth Defense has brought to the facility. Chief Engineer Teodor Weiss, who came up from the Hestia shipyards, maintains the fusion reactors and life support systems with the kind of intimate knowledge that can only come from years of working with machinery that cannot be allowed to fail.\n\nThe station's archives tell a more complex story than the official histories suggest. Records indicate discrepancies in the founding dates, missing personnel from early manifests, and gaps in the timeline that speak to the messy reality of building civilization in space. What appears clean and purposeful in retrospect was often improvised, adapted, and occasionally covered up when things went wrong.\n\nPerhaps most telling is how space infrastructure shapes the rhythms of human life. On Aegis, time is marked not by sunrise and sunset but by the 47-hour cycle of the Halion anomaly. The station's 187 current residents live by watch rotations and maintenance schedules, their lives synchronized to the needs of the machines that keep them alive. When the pulse emerges from Halion's depths, elevator doors cycle unprompted and medical monitors briefly flatline—small reminders that even the most sophisticated infrastructure remains vulnerable to forces beyond human control.\n\nThis is the reality of space infrastructure: it is simultaneously humanity's greatest achievement and its most fragile creation, capable of sustaining life across interstellar distances while remaining dependent on the dedication of engineers, the reliability of fusion reactors, and the careful balance of a thousand interconnected systems. In the end, our ability to build cities among the stars rests not just on advanced technology, but on the very human capacity to adapt, improvise, and persist in the face of an indifferent universe.\n\n---\n\n# Research Facilities and Operations\n\nIn the cold depths of the Kepler-186 system, where the distant star barely provides more light than a bright moon, Aegis Station represents humanity's methodical pursuit of knowledge in the face of the unknown. This Class-IV deep-space research platform orbits the gas giant Halion like a mechanical moon, its three concentric rings connected by six radial spokes creating a distinctive silhouette against the planet's swirling atmosphere. What began as a simple waystation for vessels returning from the Lyran expeditions has evolved into something far more significant—a dedicated scientific outpost wrestling with questions that challenge our understanding of the universe itself.\n\nThe station's transformation came in 2401 with the discovery of what researchers now call the Halion anomaly. Every 47 hours, give or take four minutes, an electromagnetic pulse emerges from deep within the gas giant's atmosphere and propagates outward in a spherical wavefront. For exactly 3.7 seconds, this signal occupies the hydrogen line frequency at 1420 MHz—a choice that seems almost deliberately provocative to any civilization that understands radio astronomy. The pulse's amplitude varies dramatically between events, sometimes barely registering on sensors, other times strong enough to cause elevator doors throughout the station to cycle unprompted and medical monitors to briefly flatline.\n\nWithin Aegis's middle ring, where the research laboratories cluster around the central computing core, scientists approach this mystery with the methodical rigor that defines human scientific endeavor. Dr. Anika Rho leads the Halion Anomaly Project from her laboratory, where banks of equipment continuously monitor and analyze each pulse. Her controversial 2010 paper argued that the signal exhibits non-random structure when sampled at sufficient resolution—suggesting not a natural phenomenon but a structured transmission from an intelligence dwelling within Halion's crushing depths. Dr. Elias Fen's computational xenology lab houses the signal-analysis cluster that processes this data, though his own analysis found no statistically significant patterns in the transmissions.\n\nThe station's operational procedures reflect the careful balance between scientific openness and security concerns that characterizes much of humanity's expansion into space. While Aegis officially operates as a civilian research outpost, three of its laboratories work under Commonwealth Defense classifications. The existence of these restricted facilities is publicly acknowledged—their research emphatically is not. Captain Drest Hollow maintains station security with a complement of twelve personnel rotating in shifts, and he reports directly to Commander Iresh Vale while maintaining his own private communications channel to Commonwealth Defense.\n\nResearch on Aegis proceeds under the constant awareness that every 47 hours, something unknown reaches out from the depths of Halion. The station's crew of 187—scientists, engineers, security personnel, and support staff—have adapted their routines around this rhythm. Dr. Saoirse Lang, originally assigned to propulsion research, has found herself pulled into anomaly work for months as the mystery deepens. Chief Engineer Teodor Weiss maintains the station's fusion reactor and life support systems while investigating whether the 2407 reactor scram that occurred eleven seconds after a Halion pulse represents mere coincidence or something more troubling.\n\nIn the restricted archives of the inner ring, Archivist Teague Marr maintains the station's records with the thoroughness of someone who understands that institutional memory can be fragile. His work has uncovered discrepancies in Aegis's official history—dates that don't align, personnel records that seem sanitized, gaps that suggest the station's early years were more complex than the public timeline indicates. These discoveries raise questions about what happened during Aegis's founding era and why someone felt compelled to obscure those details.\n\nThe methodologies employed on Aegis reflect the careful, incremental approach that characterizes human scientific advancement. Automated probes drop into Halion's upper atmosphere to gather data from as close to the source as possible. The signal-analysis cluster processes terabytes of information from each pulse, searching for patterns that might reveal the anomaly's nature. Materials research continues in parallel, as scientists investigate whether the emissions might provide insights into exotic physics or previously unknown forms of matter.\n\nCommander Vale oversees this complex operation from the command deck, where she has spent increasingly long hours since what station personnel refer to simply as "the third anomaly event"—an incident significant enough to alter the station director's behavior but classified enough that its details remain restricted. The station's self-sufficient systems—hydroponic bays producing 92% of caloric needs, water reclamation operating at 99.3% efficiency, fusion reactor providing 1.8 terawatts of continuous power—allow this work to continue indefinitely in the cold reaches of space.\n\nEvery 47 hours, as the pulse emerges from Halion's depths and washes over Aegis Station, the crew pauses in their work to observe and record. Whether they are documenting the first contact with an alien intelligence or simply witnessing an exotic natural phenomenon remains the central question driving their research. The answer, when it comes, will emerge through the patient accumulation of data, the careful analysis of patterns, and the methodical application of scientific rigor that has carried humanity to the stars.\n\n---\n\n# Advanced Technology Systems\n\nThe heart of Aegis Station pulses with controlled stellar fire. Deep within the inner ring, a Kellan-class Mk IV deuterium-tritium tokamak reactor has maintained its vigil for over twenty-five years, its magnetic fields containing temperatures that rival the core of a star. This fusion powerhouse delivers an extraordinary 1.8 terawatts of continuous energy—enough to power entire planetary settlements—yet here it serves a single research station orbiting the enigmatic gas giant Halion.\n\nThe reactor's story is one of remarkable reliability in humanity's push into the outer systems. Installed when Aegis Station first came online in 2387, it has weathered the transition from waystation to research outpost without missing a beat. Its most recent comprehensive overhaul in 2405 ensured it would continue its faithful service well into the coming decades. Chief Engineer Teodor Weiss, who came up through the renowned Hestia shipyards, maintains the system with the kind of meticulous care that keeps 187 souls alive in the cold depths of space.\n\nShould the unthinkable happen, Aegis doesn't rely on a single point of failure. Two backup reactors wait in cold standby—a Kellan Mk II capable of 600 gigawatts and a robust Hestia-pattern pebble-bed fission unit rated at 200 gigawatts. The fusion backup can spin up in forty-seven minutes, while the fission unit stands ready to deliver emergency power in just eight minutes. It's a redundancy that speaks to the Commonwealth's understanding that out here, beyond the reach of rescue fleets, self-sufficiency isn't just important—it's survival.\n\nThe reactor's safety record tells a story of careful engineering and conservative operation. In twenty-five years of service, only three incidents have triggered the automated safety systems. A coolant loop overpressure in 2392 caused the first emergency shutdown, followed by an eleven-minute station-wide power interruption in 2405 traced to the central power distribution bus. Most recently, in 2407, a faulty neutron sensor caused another precautionary shutdown. In each case, the reactor's safety envelope held firm, and complete telemetry allowed engineers to understand exactly what had occurred.\n\nYet even in this triumph of human engineering, the mysteries of Halion intrude. That 2407 reactor scram occurred just eleven seconds after one of the planet's strange electromagnetic pulses—the very phenomenon that transformed Aegis from a quiet waystation into a hub of scientific inquiry. Whether this timing represents mere coincidence or something more significant remains an open question, one that adds another layer to the growing enigma surrounding the station's true purpose in this distant corner of the galaxy.\n\nThis technological infrastructure represents more than mere machinery—it embodies humanity's determination to push into the unknown while maintaining the complex life support systems that make such exploration possible. Every terawatt flowing through Aegis Station's power grid is a testament to the engineering prowess that allows human civilization to take root among the stars, even as those same stars continue to guard their secrets.\n\n---\n\n# Electromagnetic Phenomena\n\nWhen the first automated probes descended through Halion's roiling atmosphere in 2401, their sensors detected something that would fundamentally alter humanity's understanding of the Kepler-186 system. Every forty-seven hours, with clockwork precision, an electromagnetic pulse erupts from deep within the gas giant—forty thousand kilometers below its cloud deck—and spreads outward in a perfect sphere. For exactly 3.7 seconds, this mysterious signal dominates a narrow frequency band near 1420 MHz, the so-called hydrogen line that astronomers have long associated with the basic building blocks of the universe.\n\nWhat makes the Halion anomaly so unsettling isn't just its regularity, but its apparent uniqueness. In a system where three moons orbit silently and the star itself maintains electromagnetic quiet, this lone planet pulses like a cosmic heartbeat. The signal's amplitude varies dramatically—sometimes barely detectable, other times ten times stronger—yet its timing never wavers by more than four minutes. Dr. Anika Rho's controversial research suggests the waveform contains deliberate structure when examined closely enough, though her colleague Dr. Fen's analysis found no such patterns. The debate rages on, but one thing remains clear: if something intelligent created this signal, it originates from inside Halion itself.\n\nThe pulse doesn't destroy technology outright—Aegis Station continues to function normally between events—but its effects ripple through every electromagnetic system in range. During each 3.7-second transmission, the station becomes a theater of minor chaos: elevator doors cycle open and closed without command, medical monitors flatline briefly before resuming normal readings, and the central computing core drops handfuls of processes like a juggler momentarily distracted. These aren't random failures but consistent, repeatable phenomena that suggest the anomaly interacts with technology in ways engineers are still struggling to understand.\n\nPerhaps most troubling was the reactor incident of 2407, when Aegis Station's main fusion reactor executed an emergency shutdown just eleven seconds after a Halion pulse. Chief Engineer Weiss maintains that the correlation might be coincidental—sensor faults happen, after all—but it marked the first time the anomaly appeared to affect critical infrastructure. The reactor's safety systems worked perfectly, but the implications sent ripples through Commonwealth Defense that are still being felt years later.\n\nThe electromagnetic phenomena surrounding Halion have transformed what was once a quiet waystation into humanity's most closely watched outpost. Where expeditions once stopped briefly for fuel and supplies, teams of researchers now monitor every pulse, cataloging variations and searching for patterns that might explain whether they're witnessing a natural phenomenon or something far more profound. The Commonwealth's decision to extend the classification on anomaly data suggests they're taking no chances with whatever secrets Halion might be broadcasting to the cosmos, one perfectly timed pulse at a time.\n\n---\n\n# Personnel and Organization\n\nIn the vast emptiness between stars, where the nearest help might be months away, the way people organize themselves becomes a matter of survival as much as efficiency. Aegis Station, hanging in the shadow of the gas giant Halion, offers a perfect window into how humanity has adapted its age-old hierarchies and responsibilities to the unique demands of deep space.\n\nAt first glance, the station's organizational chart might seem familiar to anyone who has worked in a large institution. Commander Iresh Vale sits at the top as Station Director, with Executive Officer Maren Koval handling the grinding machinery of day-to-day operations. Below them, departments branch out in predictable patterns: Science Division, Security, Engineering, Medical. But look closer, and the peculiarities of space-based living begin to emerge.\n\nConsider Chief Engineer Teodor Weiss, who came up through the Hestia shipyards and has earned a reputation for fixing things nobody asked him to fix. In terrestrial organizations, such initiative might be discouraged or channeled through proper procedures. Here, where a failing life support system or reactor malfunction could kill everyone aboard, that kind of proactive engineering isn't just tolerated—it's essential. The margin for error is so thin that traditional bureaucratic boundaries often blur out of necessity.\n\nThe Science Division reveals another adaptation: the fluid nature of assignments when crisis demands it. Dr. Saoirse Lang was technically assigned to propulsion research, but the Halion anomaly has pulled her into entirely different work for the past eight months. In a terrestrial research institution, such a reassignment might require committees, budget transfers, and months of administrative maneuvering. On Aegis, it simply happens because the work needs doing and she has the skills to do it.\n\nPerhaps most telling is the way security operates in this environment. Captain Drest Hollow maintains a private communications channel directly to Commonwealth Defense—a level of autonomy that speaks to the unique challenges of maintaining order and safety when you're months away from any backup. His twelve security personnel rotate in shifts of four, a ratio that might seem light for a facility housing nearly two hundred people, until you consider that there's literally nowhere to run in space. The ocean of vacuum itself becomes the ultimate deterrent.\n\nThe presence of civilians like Archivist Teague Marr adds another layer of complexity. Marr's nominal job is organizing restricted archives, but his logs suggest he possesses an unusual breadth of knowledge about the station's history. In space, where every person aboard represents a significant investment in transport costs and life support resources, it's common for individuals to wear multiple hats or possess expertise that extends well beyond their official duties.\n\nMedical Officer Ori Sato embodies this reality starkly—as the only qualified surgeon on station, she works entirely alone. There are no colleagues to consult, no specialists to call in for complex cases. The weight of every medical decision falls on her shoulders, a responsibility that would be unthinkable in most terrestrial facilities but becomes grimly necessary when the nearest hospital is light-years away.\n\nThe station's command structure has evolved to handle these realities through what might be called "distributed expertise." While Commander Vale maintains overall authority, she's described as rarely leaving the command deck since "the third anomaly event"—a detail that hints at how crisis management in space can fundamentally alter normal hierarchical relationships. When the Executive Officer runs "a tight watch rotation" and the Station Director focuses intensely on specific threats, you're seeing an organization that has learned to flex and adapt its leadership structure to meet the demands of the moment.\n\nThis flexibility extends to the boundaries between military and civilian authority. Though Aegis is officially listed as a civilian research outpost, Commonwealth Defense maintains a visible presence and classified laboratories. The interplay between scientific curiosity and military necessity creates a unique organizational culture where a former xenolinguist can command a station while defense officials maintain their own channels of communication and authority.\n\nWhat emerges from this structure is a picture of human organization stripped down to its essential functions and rebuilt for an environment where failure isn't just professional embarrassment—it's death. Every role carries weight beyond its formal description, every person becomes critical to the whole, and the traditional boundaries between departments become permeable when survival is at stake. It's humanity learning to govern itself in the void, one station at a time.\n\n---\n\n# Scientific Research Programs\n\nIn the vast emptiness surrounding the gas giant Halion, Aegis Station pulses with the quiet intensity of minds at work. Every 47 hours, as regular as clockwork, an electromagnetic signal erupts from deep within the planet's atmosphere—and with each pulse, the researchers aboard this remote outpost edge closer to questions that may reshape humanity's understanding of the universe.\n\nThe Halion Anomaly Project dominates the station's scientific efforts, transforming what was once a simple waystation into a crucible of discovery. Dr. Anika Rho leads the investigation with fierce dedication, her controversial 2410 paper arguing that the recurring 3.7-second pulse isn't natural at all, but rather a structured transmission from something—or someone—hidden beneath Halion's churning clouds. The signal emerges from the hydrogen line frequency, that fundamental wavelength scientists have long associated with the building blocks of cosmic communication.\n\nYet science thrives on disagreement, and Dr. Elias Fen's computational analysis tells a different story. His signal-analysis cluster in the station's central core has found no meaningful structure in the transmissions, despite testing at every resolution imaginable. The debate between Rho and Fen represents more than academic rivalry—it embodies the fundamental question of whether humanity stands alone in this corner of the galaxy.\n\nThe anomaly's effects ripple through the station itself in subtle but unsettling ways. During each pulse, elevator doors cycle without command, medical monitors briefly flatline, and the central computer drops processes like a mind momentarily distracted. Most troubling was the 2407 reactor scram that occurred just eleven seconds after a Halion pulse—a correlation that Chief Engineer Teodor Weiss continues investigating, though he maintains the reactor's safety envelope was never truly threatened.\n\nDr. Saoirse Lang, originally assigned to propulsion research, has found herself drawn into the anomaly work for eight months now, her materials expertise proving unexpectedly valuable as the team grapples with electromagnetic phenomena that seem to bend conventional understanding. The collaborative nature of the research reflects the mystery's complexity—no single discipline holds all the answers.\n\nBehind the scenes, however, the research unfolds under increasingly watchful eyes. Three laboratories now operate under Commonwealth Defense classifications, their work acknowledged but not disclosed. The Defense classification on anomaly data was quietly extended in 2411 with no timeline for public release, while Captain Drest Hollow maintains his private communication channel to Commonwealth Defense headquarters.\n\nEven the station's archives hold secrets that complicate the research picture. Archivist Teague Marr, nominally a civilian contractor organizing restricted files, has uncovered troubling inconsistencies in Aegis Station's founding records—discrepancies in dates, missing personnel, and gaps in the official history that suggest the station's true purpose may have been classified from the very beginning.\n\nCommander Iresh Vale, the former xenolinguist who now directs the station, has grown increasingly reclusive since the third anomaly event, rarely leaving the command deck. Her background in xenolinguistics proves particularly relevant as the team grapples with the possibility that they're not just observing a natural phenomenon, but potentially receiving a message from an intelligence that defies current understanding.\n\nThe research continues with methodical precision, each pulse monitored and analyzed, each data point added to the growing corpus of knowledge. Whether the Halion anomaly represents first contact, an unknown natural phenomenon, or something else entirely, the scientists of Aegis Station stand at the frontier of discovery, their work unfolding in the shadow of a gas giant that keeps its secrets 40,000 kilometers below the clouds.\n\n---\n\n# Operational Protocols\n\nWhen you first step aboard Aegis Station, the most striking thing isn't the view of Halion's swirling storms through the observation deck windows—it's the sound of the place breathing. The life support systems hum with mechanical precision, recycling every drop of moisture from the air at a remarkable 99.3% efficiency rate. This isn't just impressive engineering; it's survival made audible. Out here in the outer reaches of the Kepler-186 system, there are no second chances.\n\nExecutive Officer Maren Koval runs the day-to-day operations with the discipline of her thirty-year Navy service record, maintaining what everyone calls "a tight watch rotation." The station operates on shifts that account for both human needs and the peculiar rhythm of their research subject—that mysterious pulse emerging from Halion every 47 hours. Personnel learn quickly that routine is everything when you're supporting 187 souls in the deep black, even though the station could theoretically house 214.\n\nThe fusion reactor at Aegis's heart represents both the station's greatest strength and its most carefully managed risk. Chief Engineer Teodor Weiss, who came up through the Hestia shipyards, oversees a Kellan-class Mk IV tokamak that has been running since 2387. The reactor has never breached its safety envelope, though it has experienced two major scrams—automated shutdowns that Weiss describes with the matter-of-fact tone of someone who understands that in space, paranoid systems keep people alive. Two backup reactors wait in cold standby, ready to spin up in 47 minutes or 8 minutes depending on which one is needed.\n\nWhat makes Aegis unusual among research stations is how the anomaly has shaped its operational rhythm. Every 47 hours, that electromagnetic pulse washes over the station, and for 3.7 seconds, small things go wrong in predictable ways. Elevator doors cycle without being called. Medical monitors briefly flatline. The central computing core drops a handful of non-critical processes. Dr. Elias Fen, who manages the signal-analysis cluster, has learned to schedule his most important computational work around these interruptions. It's become just another part of station life—like checking the atmospheric recyclers or monitoring reactor temperatures.\n\nSecurity protocols reflect the station's dual nature as both civilian research outpost and Commonwealth Defense facility. Captain Drest Hollow maintains twelve security personnel in rotating shifts of four, though their exact duties remain opaque to most of the crew. Three laboratories operate under Defense classifications, their research acknowledged but not discussed. Hollow reports directly to Commander Vale and maintains what everyone knows is a private communications channel to Commonwealth Defense—a reminder that even in the outer systems, some research attracts attention from the inner worlds.\n\nThe station's self-sufficiency extends beyond technical systems to the careful management of information itself. Archivist Teague Marr, officially a civilian contractor responsible for organizing the restricted archives, has developed an encyclopedic knowledge of station records that seems to exceed what his nominal duties would require. His work has uncovered discrepancies in the official histories—construction dates that don't align, personnel records that seem to have gaps—but these discoveries tend to prompt uncomfortable conversations that end with people changing the subject.\n\nPerhaps most tellingly, the station operates with only one qualified surgeon, Dr. Ori Sato, who works alone in the medical bay. This isn't unusual for a research outpost, but it underscores a fundamental truth about life on Aegis: everything depends on systems working as designed, people following protocols, and the careful maintenance of routines that keep a small community functional in an environment where the nearest help is months away. Commander Vale, rarely seen outside the command deck since what people carefully call "the third anomaly event," has created a command structure that runs smoothly in her absence—perhaps by necessity, perhaps by design.\n\nThe hydroponic bays that provide 92% of the station's food operate on schedules as precise as the reactor maintenance logs. Water reclamation, atmospheric processing, waste management, power distribution—each system interlocks with the others in ways that make Aegis less like a workplace and more like a carefully balanced ecosystem. The personnel don't just work here; they inhabit it, and their protocols reflect the understanding that in space, the distinction between operational procedure and survival skill becomes meaningless.	completed	\N	2026-04-20 05:31:50.637258	2026-04-20 05:36:00.708062
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: contradictions contradictions_pkey; Type: CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.contradictions
    ADD CONSTRAINT contradictions_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: projects projects_name_key; Type: CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_name_key UNIQUE (name);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: syntheses syntheses_pkey; Type: CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.syntheses
    ADD CONSTRAINT syntheses_pkey PRIMARY KEY (id);


--
-- Name: ix_contradictions_project_id; Type: INDEX; Schema: public; Owner: canon_user
--

CREATE INDEX ix_contradictions_project_id ON public.contradictions USING btree (project_id);


--
-- Name: ix_syntheses_project_id; Type: INDEX; Schema: public; Owner: canon_user
--

CREATE INDEX ix_syntheses_project_id ON public.syntheses USING btree (project_id);


--
-- Name: uq_contradictions_pair; Type: INDEX; Schema: public; Owner: canon_user
--

CREATE UNIQUE INDEX uq_contradictions_pair ON public.contradictions USING btree (project_id, LEAST(chunk_a_id, chunk_b_id), GREATEST(chunk_a_id, chunk_b_id));


--
-- Name: contradictions contradictions_document_a_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.contradictions
    ADD CONSTRAINT contradictions_document_a_id_fkey FOREIGN KEY (document_a_id) REFERENCES public.documents(id) ON DELETE SET NULL;


--
-- Name: contradictions contradictions_document_b_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.contradictions
    ADD CONSTRAINT contradictions_document_b_id_fkey FOREIGN KEY (document_b_id) REFERENCES public.documents(id) ON DELETE SET NULL;


--
-- Name: contradictions contradictions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.contradictions
    ADD CONSTRAINT contradictions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: documents fk_documents_project_id; Type: FK CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_documents_project_id FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: syntheses syntheses_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: canon_user
--

ALTER TABLE ONLY public.syntheses
    ADD CONSTRAINT syntheses_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 96htZBq2dR4aVTJN6GzWpoU9OIcz3jAFqhQV99aUi0PqsiOoZJONAIsPMQQEL4z


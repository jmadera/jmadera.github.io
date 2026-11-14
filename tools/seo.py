# -*- coding: utf-8 -*-
"""SEO / AI-search layer: per-page metadata, JSON-LD, sitemap.xml, robots.txt, llms.txt, 404.html.
Se ejecuta al final de build_site.py (idempotente)."""
import datetime, html, json, os, re, subprocess

SITE = 'https://jmadera.github.io'
PERSON_ID = SITE + '/#julio-madera'
OG_IMAGE = SITE + '/images/og-card.jpg'
ORCID = 'https://orcid.org/0000-0001-5551-690X'
SCHOLAR = 'https://scholar.google.com/citations?user=cGe6Tv0AAAAJ&hl=en'
SAME_AS = [ORCID, SCHOLAR, 'https://github.com/jmadera']
TODAY = datetime.date.today().isoformat()

# file -> (title <=60 chars, description <=160 chars, crumb, priority, changefreq)
PAGES = {
 'index.html': ('Julio Madera | AI, Machine Learning & Optimization Researcher',
   'Julio César Madera Quintana, Full Professor and Rector at the University of Camagüey, Cuba. Research in artificial intelligence, machine learning, optimization and estimation of distribution algorithms.', 'Home', '1.0', 'monthly'),
 'research.html': ('Research: Estimation of Distribution Algorithms | Julio Madera',
   'Research lines of Julio Madera: estimation of distribution algorithms (EDAs), machine learning, optimization, energy systems and natural language processing, with publication trends by year.', 'Research', '0.9', 'monthly'),
 'publications.html': ('Publications | Julio Madera',
   'Complete list of publications by Julio Madera Quintana: journal articles, conference papers, book chapters and software registrations, newest first (1999–2026), with search and year filter.', 'Publications', '0.9', 'weekly'),
 'events.html': ('Scientific Events & Conferences | Julio Madera',
   'Conferences, workshops and contests attended or presented by Julio Madera, from 1998 to 2026, ordered from newest to oldest.', 'Events', '0.6', 'monthly'),
 'talks.html': ('Talks and Lectures | Julio Madera',
   'Lectures and talks by Julio Madera on artificial intelligence, optimization, heritage cities and education (2020–2026).', 'Talks', '0.6', 'monthly'),
 'projects.html': ('Research Projects | Julio Madera',
   'Research projects and applications led or joined by Julio Madera: VLIR TIC, energy-resource management, AI in education and applied machine learning.', 'Projects', '0.6', 'monthly'),
 'teaching.html': ('Postgraduate Teaching | Julio Madera',
   'Postgraduate courses taught by Julio Madera since 1998: advanced programming, discrete and computational mathematics, artificial intelligence and big data.', 'Teaching', '0.6', 'yearly'),
 'supervision.html': ('Supervised Doctoral and Master’s Theses | Julio Madera',
   'Doctoral and master’s theses supervised by Julio Madera on estimation of distribution algorithms, optimization, deep learning and imbalanced learning.', 'Supervision', '0.6', 'yearly'),
 'leadership.html': ('Academic Leadership | Julio Madera',
   'Academic and scientific leadership of Julio Madera: Rector and Vice-Rector at the University of Camagüey, national PhD committee, editorial and society roles.', 'Leadership', '0.5', 'yearly'),
 'awards.html': ('Awards and Recognitions | Julio Madera',
   'Awards of Julio Madera: Cuban Academy of Sciences Award 2023, GECCO and IEEE WCCI energy-domain competition wins, Pablo Miquel Award.', 'Awards', '0.7', 'yearly'),
 'competitions.html': ('Competitions and Shared Tasks | Julio Madera',
   'Results in GECCO and IEEE competitions on evolutionary computation in the energy domain, and shared-task participation at IberLEF and Rest-Mex.', 'Competitions', '0.6', 'monthly'),
 'cv.html': ('Curriculum Vitae (PDF, English & Spanish) | Julio Madera',
   'Curriculum vitae of Julio César Madera Quintana: education, positions, publications, awards and supervision. Download the PDF in English or Spanish.', 'CV', '0.8', 'monthly'),
 'contact.html': ('Contact | Julio Madera',
   'Contact Julio Madera for research collaboration, teaching or academic inquiries. Email, ORCID, Google Scholar and GitHub.', 'Contact', '0.5', 'yearly'),
}
REDIRECTS = {'postgraduate-courses.html', 'responsibilities.html'}

def url_of(name): return SITE + '/' if name == 'index.html' else f'{SITE}/{name}'

def person():
    return {
      '@type': 'Person', '@id': PERSON_ID, 'name': 'Julio César Madera Quintana',
      'alternateName': ['Julio Madera', 'Julio C. Madera', 'J. Madera', 'Madera Quintana, Julio César'],
      'honorificPrefix': 'Dr.', 'url': SITE + '/', 'image': SITE + '/images/profile.jpg',
      'email': 'mailto:julio.madera@reduc.edu.cu',
      'jobTitle': ['Rector', 'Full Professor'],
      'description': 'Cuban computer scientist working on artificial intelligence, machine learning, optimization and estimation of distribution algorithms.',
      'nationality': {'@type': 'Country', 'name': 'Cuba'},
      'worksFor': {'@type': 'CollegeOrUniversity', 'name': 'University of Camagüey', 'alternateName': 'Universidad de Camagüey',
                   'address': {'@type': 'PostalAddress', 'addressLocality': 'Camagüey', 'addressCountry': 'CU', 'postalCode': '74650'}},
      'alumniOf': [
        {'@type': 'CollegeOrUniversity', 'name': 'Institute of Cybernetics, Mathematics and Physics (ICIMAF)'},
        {'@type': 'CollegeOrUniversity', 'name': 'University of Camagüey'},
        {'@type': 'CollegeOrUniversity', 'name': 'Central University of Las Villas'}],
      'hasCredential': [{'@type': 'EducationalOccupationalCredential', 'name': 'Doctor of Mathematical Sciences', 'credentialCategory': 'degree'}],
      'knowsAbout': ['Artificial intelligence', 'Machine learning', 'Optimization', 'Estimation of distribution algorithms',
                     'Evolutionary computation', 'Metaheuristics', 'Natural language processing', 'Imbalanced learning', 'Energy systems optimization'],
      'knowsLanguage': ['es', 'en'], 'sameAs': SAME_AS,
    }

def jsonld(name, title, desc, crumb):
    graph = []
    if name == 'index.html':
        graph.append({'@type': 'WebSite', '@id': SITE + '/#website', 'url': SITE + '/', 'name': 'Julio Madera | Research Portfolio',
                      'inLanguage': ['en', 'es'], 'publisher': {'@id': PERSON_ID}})
        graph.append({'@type': 'ProfilePage', '@id': SITE + '/#profile', 'url': SITE + '/', 'name': title, 'description': desc,
                      'inLanguage': ['en', 'es'], 'isPartOf': {'@id': SITE + '/#website'}, 'mainEntity': person(),
                      'primaryImageOfPage': {'@type': 'ImageObject', 'url': OG_IMAGE, 'width': 1200, 'height': 630}})
    else:
        ptype = 'CollectionPage' if name in ('publications.html', 'events.html', 'awards.html', 'competitions.html', 'talks.html', 'supervision.html') else 'WebPage'
        graph.append({'@type': ptype, '@id': url_of(name) + '#page', 'url': url_of(name), 'name': title, 'description': desc,
                      'inLanguage': ['en', 'es'], 'isPartOf': {'@id': SITE + '/#website'}, 'about': {'@id': PERSON_ID}})
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': crumb, 'item': url_of(name)}]})
        if name == 'cv.html':
            graph.append({'@type': 'DigitalDocument', 'name': 'Curriculum Vitae of Julio Madera (English)', 'encodingFormat': 'application/pdf',
                          'url': SITE + '/files/julio_madera_en.pdf', 'inLanguage': 'en', 'author': {'@id': PERSON_ID}})
            graph.append({'@type': 'DigitalDocument', 'name': 'Currículum Vitae de Julio Madera (Español)', 'encodingFormat': 'application/pdf',
                          'url': SITE + '/files/julio_madera_es.pdf', 'inLanguage': 'es', 'author': {'@id': PERSON_ID}})
        graph.append({'@id': PERSON_ID, **{k: v for k, v in person().items() if k in ('@type', 'name', 'url')}})
    return '<script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')) + '</script>'

def head_block(name):
    title, desc, crumb, *_ = PAGES[name]
    e = lambda s: html.escape(s, quote=True)
    u = url_of(name)
    return f'''<!--seo-->
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <meta name="author" content="Julio César Madera Quintana">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <link rel="canonical" href="{u}">
  <meta property="og:type" content="{'profile' if name == 'index.html' else 'website'}">
  <meta property="og:site_name" content="Julio Madera | Research Portfolio">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:url" content="{u}">
  <meta property="og:locale" content="en_US">
  <meta property="og:locale:alternate" content="es_ES">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Julio Madera, researcher in artificial intelligence and optimization">
  {'<meta property="profile:first_name" content="Julio César"><meta property="profile:last_name" content="Madera Quintana">' if name == 'index.html' else ''}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{e(title)}">
  <meta name="twitter:description" content="{e(desc)}">
  <meta name="twitter:image" content="{OG_IMAGE}">
  <link rel="me" href="{ORCID}">
  <link rel="me" href="https://github.com/jmadera">
  {jsonld(name, title, desc, crumb)}
<!--/seo-->'''

STRIP = [r'\s*<title>.*?</title>', r'\s*<meta name="description"[^>]*>', r'\s*<meta name="author"[^>]*>', r'\s*<meta name="robots"[^>]*>',
         r'\s*<link rel="canonical"[^>]*>', r'\s*<meta property="og:[^>]*>', r'\s*<meta property="profile:[^>]*>', r'\s*<meta name="twitter:[^>]*>',
         r'\s*<link rel="me"[^>]*>', r'\s*<script type="application/ld\+json">.*?</script>', r'\s*<!--seo-->.*?<!--/seo-->']

def lang_spans(src):
    src = re.sub(r'<span class="es"(?! lang)', '<span class="es" lang="es"', src)
    return re.sub(r'<span class="en"(?! lang)', '<span class="en" lang="en"', src)

def git_date(name):
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', name], capture_output=True, text=True, cwd=ROOT).stdout.strip()
        dirty = subprocess.run(['git', 'status', '--porcelain', '--', name], capture_output=True, text=True, cwd=ROOT).stdout.strip()
        return TODAY if (dirty or not out) else out
    except Exception:
        return TODAY

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def W(name, text):
    with open(os.path.join(ROOT, name), 'w', encoding='utf-8', newline='\n') as f: f.write(text)

def apply_pages():
    for name in PAGES:
        p = os.path.join(ROOT, name)
        src = open(p, encoding='utf-8').read().replace('\r\n', '\n')
        for rx in STRIP: src = re.sub(rx, '', src, flags=re.S)
        src = re.sub(r'(<meta name="viewport"[^>]*>)', lambda m: m.group(1) + '\n  ' + head_block(name), src, count=1)
        src = lang_spans(src)
        W(name, src)
    for name in REDIRECTS:   # redirect stubs: keep out of the index
        p = os.path.join(ROOT, name)
        src = open(p, encoding='utf-8').read()
        if 'name="robots"' not in src:
            src = src.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n  <meta name="robots" content="noindex, follow">', 1)
        W(name, src)

def sitemap():
    rows = []
    for name, (t, d, c, pr, cf) in PAGES.items():
        rows.append(f'  <url><loc>{url_of(name)}</loc><lastmod>{git_date(name)}</lastmod><changefreq>{cf}</changefreq><priority>{pr}</priority></url>')
    for f in ('julio_madera_en.pdf', 'julio_madera_es.pdf'):
        rows.append(f'  <url><loc>{SITE}/files/{f}</loc><lastmod>{git_date("files/" + f)}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>')
    W('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(rows) + '\n</urlset>\n')

def robots():
    ai = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'anthropic-ai', 'PerplexityBot', 'Perplexity-User',
          'Google-Extended', 'Applebot', 'Applebot-Extended', 'Bingbot', 'DuckAssistBot', 'CCBot', 'cohere-ai', 'Meta-ExternalAgent', 'Bytespider']
    txt = '# Everything is public and welcome to be indexed, including AI search and assistant crawlers.\n# To opt out of AI *training* only, change Allow to Disallow for GPTBot, Google-Extended, CCBot, anthropic-ai, ClaudeBot, Applebot-Extended.\n\nUser-agent: *\nAllow: /\n\n'
    txt += ''.join(f'User-agent: {b}\nAllow: /\n\n' for b in ai)
    txt += f'Sitemap: {SITE}/sitemap.xml\n'
    W('robots.txt', txt)

def llms():
    L = [f'# Julio César Madera Quintana (Julio Madera)', '',
 '> Cuban computer scientist, Rector and Full Professor at the University of Camagüey (Cuba). Doctor of Mathematical Sciences (ICIMAF, 2010). Research in artificial intelligence, machine learning, optimization and estimation of distribution algorithms (EDAs), including cellular and parallel EDAs, applications to energy systems, imbalanced learning, natural language processing and education.', '',
 'Key facts:',
 '- Name variants: Julio Madera, Julio César Madera Quintana, J. Madera, Madera Quintana J.',
 '- Affiliation: Universidad de Camagüey, Camagüey, Cuba. Positions: Rector (2025–present), First Vice-Rector (2021–2025), Vice-Rector for Informatization (2017–2020), Dean of the Faculty of Informatics (2012–2016).',
 '- Education: PhD Mathematical Sciences (ICIMAF, 2010); MSc Applied Informatics (University of Camagüey, 2007); BSc Computer Science (Central University of Las Villas, 1997).',
 '- Awards: Cuban Academy of Sciences Award 2023 (two awards); first place GECCO 2023, 2021 and 2020 energy-domain competitions; Pablo Miquel Award 2021; CITMA Provincial Award 2022.',
 '- Identifiers: ORCID 0000-0001-5551-690X; Google Scholar user cGe6Tv0AAAAJ; GitHub jmadera.',
 '- Languages of the site: English (default) and Spanish. Email: julio.madera@reduc.edu.cu', '',
 '## Main pages', '',
 f'- [Home / profile]({SITE}/): overview, selected publications, trajectory',
 f'- [Research]({SITE}/research.html): research lines and publications per year by topic',
 f'- [Publications]({SITE}/publications.html): full list, newest first, with DOIs and links',
 f'- [Events]({SITE}/events.html): conferences, workshops and contests, 1998–2026',
 f'- [Talks]({SITE}/talks.html): lectures and talks',
 f'- [Awards]({SITE}/awards.html): awards and recognitions',
 f'- [Competitions]({SITE}/competitions.html): GECCO/IEEE competitions and IberLEF/Rest-Mex shared tasks',
 f'- [Supervision]({SITE}/supervision.html): doctoral and master’s theses supervised',
 f'- [Teaching]({SITE}/teaching.html): postgraduate courses taught',
 f'- [Leadership]({SITE}/leadership.html): academic and scientific responsibilities',
 f'- [Projects]({SITE}/projects.html): research projects and applications',
 f'- [Contact]({SITE}/contact.html): email and academic profiles', '',
 '## Curriculum vitae (PDF)', '',
 f'- [CV in English]({SITE}/files/julio_madera_en.pdf)',
 f'- [CV en español]({SITE}/files/julio_madera_es.pdf)', '',
 '## Profiles', '',
 f'- [ORCID]({ORCID})', f'- [Google Scholar]({SCHOLAR})', '- [GitHub](https://github.com/jmadera)', '']
    W('llms.txt', '\n'.join(L))

def page404():
    src = open(os.path.join(ROOT, 'contact.html'), encoding='utf-8').read()
    src = re.sub(r'\s*<!--seo-->.*?<!--/seo-->', '', src, flags=re.S)
    src = src.replace('<link rel="stylesheet" href="style.css">', '<link rel="stylesheet" href="/style.css">')
    src = src.replace('<link rel="manifest" href="site.webmanifest">', '<link rel="manifest" href="/site.webmanifest">')
    src = re.sub(r'(<meta name="viewport"[^>]*>)', r'\1\n  <meta name="robots" content="noindex">\n  <title>Page not found | Julio Madera</title>', src, count=1)
    src = re.sub(r'href="(?!https?:|mailto:|#|/)([^"]+)"', r'href="/\1"', src)
    src = src.replace('src="script.js"', 'src="/script.js"').replace('src="images/', 'src="/images/')
    main = ('<main class="site-main" id="main-content">\n  <header class="page-header"><p class="meta">404</p>'
            '<h1><span class="es" lang="es">Página no encontrada</span><span class="en" lang="en">Page not found</span></h1>'
            '<p><span class="es" lang="es">La página que busca no existe o cambió de dirección.</span><span class="en" lang="en">The page you are looking for does not exist or has moved.</span></p>'
            '<div class="button-row"><a class="button" href="/"><span class="es" lang="es">Ir al inicio</span><span class="en" lang="en">Go to the home page</span></a>'
            '<a class="button secondary" href="/publications.html"><span class="es" lang="es">Publicaciones</span><span class="en" lang="en">Publications</span></a></div></header>\n</main>')
    src = re.sub(r'<main.*?</main>', lambda m: main, src, count=1, flags=re.S)
    W('404.html', src)

def run():
    apply_pages(); sitemap(); robots(); llms(); page404()
    print('SEO: pages', len(PAGES), '| sitemap, robots, llms.txt, 404 written')

# -*- coding: utf-8 -*-
"""Genera las páginas dinámicas del sitio y los PDF del CV a partir de curriculo.docx.
Uso:  python3 tools/build_site.py          (páginas + PDF)
      python3 tools/build_site.py --no-pdf (solo páginas)
"""
import html, os, re, subprocess, sys, tempfile
import docx
from docx.oxml.ns import qn
sys.path.insert(0, os.path.dirname(__file__))
import cvdata as D

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ORCID = 'https://orcid.org/0000-0001-5551-690X'
SCHOLAR = 'https://scholar.google.com/citations?user=cGe6Tv0AAAAJ&hl=en'
SCHOLAR_ES = 'https://scholar.google.com/citations?user=cGe6Tv0AAAAJ&hl=es'
def profile_buttons(cls='secondary'):
    return (f'<a class="button {cls}" href="{ORCID}" target="_blank" rel="noopener">ORCID</a>'
            f'<a class="button {cls}" href="{SCHOLAR_ES}" target="_blank" rel="noopener">Google Scholar</a>')
def P(*a): return os.path.join(ROOT, *a)

# ------------------------------------------------------------------ read docx
def read_lines():
    d = docx.Document(P('curriculo.docx'))
    out = []
    for b in d.element.body.iterchildren():
        if b.tag == qn('w:p'):
            t = ''.join(x.text or '' for x in b.iter(qn('w:t'))).strip()
            if t: out.append(t)
        elif b.tag == qn('w:tbl'):
            for r in b.iter(qn('w:tr')):
                out.append(' | '.join(''.join(x.text or '' for x in c.iter(qn('w:t'))) for c in r.iter(qn('w:tc'))))
    return out

L = read_lines()
def section(start, end):
    i = next(k for k, t in enumerate(L) if t.startswith(start))
    j = next(k for k, t in enumerate(L) if k > i and t.startswith(end))
    return [t.strip() for t in L[i + 1:j]]

PUBS_RAW = section('Publicaciones', 'Libros y Cap')
BOOKS_RAW = section('Libros y Cap', 'Registros y Patentes')
SOFT_RAW = section('Registros y Patentes', 'Tesis de Doctorado')
assert len(PUBS_RAW) == 88 and len(BOOKS_RAW) == 4 and len(SOFT_RAW) == 6, (len(PUBS_RAW), len(BOOKS_RAW), len(SOFT_RAW))

# ------------------------------------------------------------------ year logic
YEAR_OVERRIDE = {  # primeras palabras -> año (entradas sin año explícito en el CV)
    'A. Ochoa, M. Soto, R. Santana': 1999,   # Second Symposium on AI (CIMAF 99)
}
def clean_for_year(t):
    s = re.sub(r'https?://\S+', '', t); s = re.sub(r'doi:\s*10\.\S+', '', s, flags=re.I)
    s = re.sub(r'IS[BS]N[:\s]*[\d\-X/]+', '', s)
    s = re.sub(r'RNPS:\s*\d+', '', s)
    return s

def year_of(t):
    for k, y in YEAR_OVERRIDE.items():
        if t.startswith(k): return y
    s = clean_for_year(t)
    m = re.search(r'\((20[0-3]\d|19[89]\d)[a-z]?[,)]', s)
    if m: return int(m.group(1))
    ys = re.findall(r'\b(19[89]\d|20[0-3]\d)\b', s)
    return int(ys[-1]) if ys else None

def sort_desc(items):
    """items: list of (year, ...) in CV order (oldest first within a year). Newest first; stable inside a year."""
    rev = list(reversed(items))
    return sorted(rev, key=lambda x: -(x[0] if x[0] else 0))

def esc(t): return html.escape(t, quote=False)
def linkify(t):
    t = esc(t)
    t = re.sub(r'(doi:\s*)(10\.\d{4,9}/[^\s<]+?)(\.?)(?=\s|$)', lambda m: f'{m.group(1)}<a href="https://doi.org/{m.group(2)}" target="_blank" rel="noopener">{m.group(2)}</a>{m.group(3)}', t, flags=re.I)
    def rep(m):
        url = m.group(0); tail = ''
        while url and url[-1] in '.,;)': tail = url[-1] + tail; url = url[:-1]
        return f'<a href="{url}" target="_blank" rel="noopener">{url}</a>{tail}'
    return re.sub(r'https?://[^\s<]+', rep, t)

PUBS = sort_desc([(year_of(t), t) for t in PUBS_RAW])
BOOKS = sort_desc([(year_of(t), t) for t in BOOKS_RAW])
SOFT = sort_desc([(year_of(t), t) for t in SOFT_RAW])
# MOL2NET'23 aparece también en eventos del CV; se conserva solo en publicaciones.
EVENTS = sorted(D.EVENTS, key=lambda e: (-e[0], -e[1]))     # estable: conserva el orden relativo del CV
AWARDS = sorted(D.AWARDS, key=lambda e: -e[0])
PHD = sorted(D.PHD, key=lambda e: -e[0])
MASTERS = sorted(D.MASTERS, key=lambda e: -e[0])
TRAINING = sorted(D.TRAINING, key=lambda e: -e[0])

# courses taught: reuse bilingual list already on teaching.html (already newest first)
def read_courses():
    src = open(P('teaching.html'), encoding='utf-8').read()
    out = []
    for m in re.finditer(r'<li><span class="es"(?: lang="es")?>(.*?)</span><span class="en"(?: lang="en")?>(.*?)</span></li>', src, re.S):
        out.append((html.unescape(m.group(1)).strip(), html.unescape(m.group(2)).strip()))
    return out
COURSES = read_courses()
assert len(COURSES) == 39, len(COURSES)

# ------------------------------------------------------------------ page shell
NAV = [('index.html', 'Inicio', 'Home'), ('research.html', 'Investigación', 'Research'),
       ('publications.html', 'Publicaciones', 'Publications'), ('events.html', 'Eventos', 'Events'),
       ('projects.html', 'Proyectos', 'Projects'), ('teaching.html', 'Docencia', 'Teaching'),
       ('supervision.html', 'Tutorías', 'Supervision'), ('leadership.html', 'Liderazgo', 'Leadership'),
       ('awards.html', 'Premios', 'Awards'), ('cv.html', None, 'CV'), ('contact.html', 'Contacto', 'Contact')]
def nav_html():
    rows = []
    for h, es, en in NAV:
        inner = en if es is None else f'<span class="es">{es}</span><span class="en">{en}</span>'
        rows.append(f'        <a href="{h}">{inner}</a>')
    return '<div class="nav-links">\n' + '\n'.join(rows) + '\n      </div>'

def normalize_shell(src):
    src = src.replace('\r\n', '\n')
    src = src.replace('<html lang="es" data-language="es">', '<html lang="en" data-language="en">')
    src = re.sub(r'<div class="nav-links">.*?</div>', nav_html(), src, count=1, flags=re.S)
    src = src.replace('aria-label="Julio Madera, inicio"', 'aria-label="Julio Madera, home"')
    src = src.replace('<nav class="primary-nav" id="primary-nav" data-primary-nav aria-label="Navegación principal"', '<nav class="primary-nav" id="primary-nav" data-primary-nav aria-label="Primary navigation"')
    src = src.replace('<div class="utility-controls" aria-label="Preferencias"', '<div class="utility-controls" aria-label="Preferences"')
    src = src.replace('data-language-control="es" aria-pressed="true"', 'data-language-control="es" aria-pressed="false"')
    src = src.replace('data-language-control="en" aria-pressed="false"', 'data-language-control="en" aria-pressed="true"')
    src = src.replace('title="Cambiar modo de color"', 'title="Change color mode"')
    return src

def set_main(src, new_main, title=None, desc=None, canonical=None):
    head, rest = src.split('<main', 1)
    _, tail = rest.split('</main>', 1)
    page = head + '<main class="site-main" id="main-content">\n' + new_main + '\n</main>' + tail
    if title:
        page = re.sub(r'<title>.*?</title>', f'<title>{esc(title)}</title>', page)
        page = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\g<1>' + html.escape(title), page)
    if desc:
        page = re.sub(r'(<meta name="description" content=")[^"]*', r'\g<1>' + html.escape(desc), page)
        page = re.sub(r'(<meta property="og:description" content=")[^"]*', r'\g<1>' + html.escape(desc), page)
    if canonical:
        page = re.sub(r'(<link rel="canonical" href=")[^"]*', r'\g<1>https://jmadera.github.io/' + canonical, page)
        page = re.sub(r'(<meta property="og:url" content=")[^"]*', r'\g<1>https://jmadera.github.io/' + canonical, page)
    return page

def write(name, text):
    with open(P(name), 'w', encoding='utf-8', newline='\n') as f: f.write(text)

def bi(es, en, tag='span'):
    return f'<{tag} class="es">{es}</{tag}><{tag} class="en">{en}</{tag}>'
def header(meta_es, meta_en, h1_es, h1_en, p_es, p_en):
    return (f'  <header class="page-header">\n  <p class="meta">{bi(meta_es, meta_en)}</p>\n'
            f'  <h1>{bi(h1_es, h1_en)}</h1>\n  <p>{bi(p_es, p_en)}</p>\n</header>')

def year_groups(rows, render):
    """rows: list of tuples with year first, already sorted desc. Groups by year headings."""
    out, cur, items = [], object(), []
    def flush():
        if items: out.append('<ul class="archive-list">\n' + '\n'.join(items) + '\n</ul>')
    for r in rows:
        if r[0] != cur:
            flush(); items = []; cur = r[0]
            out.append(f'<h3 class="year-heading">{cur if cur else "—"}</h3>')
        items.append(render(r))
    flush()
    return '\n'.join(out)

# ------------------------------------------------------------------ pages
base = normalize_shell(open(P('cv.html'), encoding='utf-8').read())

def build_publications():
    old = open(P('publications.html'), encoding='utf-8').read().replace('\r\n', '\n')
    li = []
    for y, t in PUBS:
        li.append(f'<li data-year="{y}"><span class="item-year">{y}</span><span class="item-text">{linkify(t)}</span></li>')
    def simple(rows, key_es=None):
        return '<ul class="archive-list">\n' + '\n'.join(
            f'<li data-year="{y or ""}"><span class="item-year">{y or "n.d."}</span><span class="item-text">{linkify(t)}</span></li>' for y, t in rows) + '\n</ul>'
    main = header('Publicaciones', 'Publications', 'Producción científica', 'Scientific output',
                  'Artículos, capítulos y trabajos en actas, ordenados del más reciente al más antiguo, con búsqueda y filtro por año.',
                  'Articles, chapters and conference papers, ordered from newest to oldest, with search and year filter.')
    filters = old[old.index('<div class="filters"'):old.index('<section class="archive-section">')]
    # the old filters block ends right before the section; keep up to its closing div
    filters = filters[:filters.rindex('</div>') + 6]
    main += f'''
  <div class="archive-page">
    {filters}
    <section class="archive-section">
      <h2>{bi('Artículos y trabajos en actas', 'Articles and conference papers')}</h2>
      <p>{bi('Para una lista completa, consulte mi perfil en <a href="'+SCHOLAR_ES+'" target="_blank" rel="noopener">Google Scholar</a> u <a href="'+ORCID+'" target="_blank" rel="noopener">ORCID</a>.', 'For a complete list, please see my <a href="'+SCHOLAR_ES+'" target="_blank" rel="noopener">Google Scholar</a> or <a href="'+ORCID+'" target="_blank" rel="noopener">ORCID</a> profile.')}</p>
      <ul class="archive-list publication-list" data-publication-list>
{chr(10).join(li)}
      </ul>
    </section>
    <section class="archive-section">
      <h2>{bi('Libros y capítulos de libro', 'Books and book chapters')}</h2>
      {simple(BOOKS)}
    </section>
    <section class="archive-section">
      <h2>{bi('Registros de software', 'Software registrations')}</h2>
      <p>{bi('Registros del Centro Nacional de Derecho de Autor de Cuba.', 'Registrations at the Cuban National Copyright Center.')}</p>
      {simple(SOFT)}
    </section>
  </div>'''
    write('publications.html', set_main(base, main, 'Publications | Julio Madera', 'Publicaciones de Julio Madera: artículos, capítulos, libros y registros de software.', 'publications.html'))

def build_events():
    def render(r):
        y, m, es, en = r
        return f'<li><span class="item-text">{bi(linkify(es), linkify(en or es))}</span></li>'
    main = header('Eventos', 'Events', 'Eventos científicos', 'Scientific events',
                  'Ponencias, conferencias, talleres y competencias, del más reciente al más antiguo.',
                  'Talks, conferences, workshops and contests, from newest to oldest.')
    main += f'\n  <div class="archive-page"><section class="archive-section">\n{year_groups(EVENTS, render)}\n  </section></div>'
    write('events.html', set_main(base, main, 'Events | Julio Madera', 'Participación científica de Julio Madera en eventos, congresos y talleres.', 'events.html'))

def build_supervision():
    def r_phd(r): return f'<li><span class="item-text">{bi(esc(r[1]), esc(r[2]))}</span></li>'
    def r_ms(r): return f'<li><span class="item-text">{esc(r[1])}</span></li>'
    main = header('Tutorías', 'Supervision', 'Tesis dirigidas', 'Supervised theses',
                  'Tesis doctorales y de maestría tuteladas, del año más reciente al más antiguo.',
                  'Doctoral and master’s theses supervised, from the most recent year to the oldest.')
    main += f'''
  <div class="archive-page">
    <section class="archive-section"><h2>{bi('Tesis de doctorado', 'Doctoral theses')}</h2>
{year_groups(PHD, r_phd)}
    </section>
    <section class="archive-section"><h2>{bi('Tesis de maestría', 'Master’s theses')}</h2>
      <p>{bi('Los títulos se conservan en su idioma original.', 'Titles are kept in their original language (Spanish).')}</p>
{year_groups(MASTERS, r_ms)}
    </section>
  </div>'''
    write('supervision.html', set_main(base, main, 'Supervision | Julio Madera', 'Tesis doctorales y de maestría dirigidas por Julio Madera.', 'supervision.html'))

def build_awards():
    def render(r): return f'<li><span class="item-text">{bi(esc(r[1]), esc(r[2]))}</span></li>'
    main = header('Premios', 'Awards', 'Premios y reconocimientos', 'Awards and recognitions',
                  'Premios, distinciones y resultados en competencias, del más reciente al más antiguo.',
                  'Awards, distinctions and competition results, from newest to oldest.')
    main += f'\n  <div class="archive-page"><section class="archive-section">\n{year_groups(AWARDS, render)}\n  </section></div>'
    write('awards.html', set_main(base, main, 'Awards | Julio Madera', 'Premios y reconocimientos de Julio Madera.', 'awards.html'))

def pos_years(s, e): return f'{s} – {e}' if e else f'{s} – '
def build_leadership():
    pos = ''.join(
        f'<li><span class="item-year">{s}{"–"+str(e) if e else "–"}<span class="es">{"" if e else "actual"}</span><span class="en">{"" if e else "present"}</span></span><span class="item-text">{bi(es, en)}</span></li>\n'
        for s, e, es, en in D.POSITIONS)
    roles = ''.join(f'<li><span class="item-text">{bi(es, en)}</span></li>\n' for es, en in D.ROLES)
    main = header('Liderazgo académico', 'Academic leadership', 'Responsabilidades académicas y científicas', 'Academic and scientific responsibilities',
                  'Cargos de dirección, proyectos y participación en órganos científicos.',
                  'Management positions, projects and participation in scientific bodies.')
    main += f'''
  <div class="archive-page">
    <section class="archive-section"><h2>{bi('Cargos de dirección', 'Management positions')}</h2>
      <ul class="archive-list">
{pos}      </ul></section>
    <section class="archive-section"><h2>{bi('Responsabilidades científicas y servicio editorial', 'Scientific responsibilities and editorial service')}</h2>
      <ul class="archive-list">
{roles}      </ul></section>
  </div>'''
    write('leadership.html', set_main(base, main, 'Academic Leadership | Julio Madera', 'Cargos y responsabilidades académicas y científicas de Julio Madera.', 'leadership.html'))

def cv_blocks(lang_en=None):
    """Bloques bilingües de la página cv.html."""
    edu = ''.join(f'<li><span class="item-year">{a}–{b}</span><span class="item-text"><strong>{bi(es, en)}</strong><br>{bi(ies, ien)}</span></li>\n' for a, b, es, en, ies, ien in D.EDUCATION)
    exp = ''.join(f'<li><span class="item-year">{p.strip()}{"" if p.strip().endswith("–") is False else ""}</span><span class="item-text"><strong>{bi(es, en)}</strong><br>{bi(pes, pen)}</span></li>\n' for p, es, en, pes, pen in D.EXPERIENCE)
    exp = exp.replace('2000 –</span>', '2000–<span class="es">actual</span><span class="en">present</span></span>')
    tr = ''.join(f'<li><span class="item-year">{y}</span><span class="item-text"><strong>{bi(es, en)}</strong><br>{bi(ies, ien)}</span></li>\n' for y, es, en, ies, ien in TRAINING)
    return edu, exp, tr

def build_cv():
    edu, exp, tr = cv_blocks()
    main = header('Curriculum vitae', 'Curriculum vitae', 'CV', 'CV',
                  'Resumen del currículo y descarga de las versiones en PDF.', 'Curriculum summary and downloadable PDF versions.')
    main += f'''
  <section class="section" aria-labelledby="cv-download">
    <div class="cv-card">
      <h2 id="cv-download">{bi('Descargar curriculum vitae', 'Download curriculum vitae')}</h2>
      <p>{bi('Versión completa y actualizada en PDF (publicaciones, eventos, premios y tutorías).', 'Complete, up-to-date PDF (publications, events, awards and supervision).')}</p>
      <div class="button-row">
        <a class="button" href="files/julio_madera_en.pdf" download>CV · English (PDF)</a>
        <a class="button secondary" href="files/julio_madera_es.pdf" download>CV · Español (PDF)</a>
      </div>
    </div>
  </section>
  <div class="archive-page">
    <section class="archive-section"><h2>{bi('Formación académica', 'Education')}</h2><ul class="archive-list">
{edu}</ul></section>
    <section class="archive-section"><h2>{bi('Experiencia profesional', 'Professional experience')}</h2><ul class="archive-list">
{exp}</ul></section>
    <section class="archive-section"><h2>{bi('Idiomas', 'Languages')}</h2><ul class="archive-list">
''' + ''.join(f'<li><span class="item-text"><strong>{bi(a, b)}</strong> — {bi(c, d)}</span></li>\n' for a, b, c, d in D.LANGUAGES) + f'''</ul></section>
    <section class="archive-section"><h2>{bi('Postgrados y cursos recibidos', 'Postgraduate training received')}</h2><ul class="archive-list">
{tr}</ul></section>
    <section class="archive-section"><h2>{bi('Perfiles académicos', 'Academic profiles')}</h2>
      <div class="button-row">{profile_buttons()}</div></section>
    <section class="archive-section"><h2>{bi('Más información', 'More')}</h2>
      <div class="button-row">
        <a class="button secondary" href="publications.html">{bi('Publicaciones', 'Publications')}</a>
        <a class="button secondary" href="events.html">{bi('Eventos', 'Events')}</a>
        <a class="button secondary" href="awards.html">{bi('Premios', 'Awards')}</a>
        <a class="button secondary" href="supervision.html">{bi('Tutorías', 'Supervision')}</a>
      </div></section>
  </div>'''
    write('cv.html', set_main(base, main, 'CV | Julio Madera', 'Curriculum vitae de Julio Madera.', 'cv.html'))

def build_index():
    src = normalize_shell(open(P('index.html'), encoding='utf-8').read())
    pubs = '''    <div class="publication-spotlight">
      <article><time datetime="2026">2026</time><div><h3>Evaluation of Probabilistic Data Augmentation Models for Emotion Detection</h3><p>IWAIPR 2025, Lecture Notes in Computer Science, vol. 16328, Springer. <a href="https://doi.org/10.1007/978-3-032-11358-0_16" target="_blank" rel="noopener">DOI</a></p></div></article>
      <article><time datetime="2026">2026</time><div><h3>Pressure drop dynamics in a convective axis regenerative boiler using heavy crude oil</h3><p>Journal of Thermal Analysis and Calorimetry. <a href="https://doi.org/10.1007/s10973-026-15446-y" target="_blank" rel="noopener">DOI</a></p></div></article>
      <article><time datetime="2025">2025</time><div><h3>Aportes teóricos y prácticos de los modelos probabilísticos en la solución de problemas de optimización reales</h3><p>Anales de la Academia de Ciencias de Cuba, 15(2). <a href="https://revistaccuba.sld.cu/index.php/revacc/article/view/1935" target="_blank" rel="noopener">Link</a></p></div></article>
    </div>'''
    src = re.sub(r'    <div class="publication-spotlight">.*?\n    </div>', lambda m: pubs, src, count=1, flags=re.S)
    tl = '''    <div class="timeline">
      <article><time>2000–<span class="es">actual</span><span class="en">present</span></time><h3><span class="es">Profesor Titular</span><span class="en">Full Professor</span></h3><p><span class="es">Universidad de Camagüey. Rector desde 2025; Vicerrector Primero (2021–2025); previamente Decano de Informática, Director y Vicerrector de Informatización.</span><span class="en">University of Camagüey. Rector since 2025; First Vice-Rector (2021–2025); previously Dean of Informatics, Director and Vice-Rector of Informatization.</span></p></article>
      <article><time>2006–2010</time><h3><span class="es">Doctor en Ciencias Matemáticas</span><span class="en">Doctor of Mathematical Sciences</span></h3><p><span class="es">Instituto de Cibernética, Matemática y Física.</span><span class="en">Institute of Cybernetics, Mathematics and Physics.</span></p></article>
      <article><time>2005–2007</time><h3><span class="es">Máster en Informática Aplicada</span><span class="en">Master’s in Applied Informatics</span></h3><p><span class="es">Universidad de Camagüey.</span><span class="en">University of Camagüey.</span></p></article>
      <article><time>1997–2000</time><h3><span class="es">Experiencia profesional</span><span class="en">Professional experience</span></h3><p><span class="es">Administración de redes, atención a sistemas económicos y soporte a usuarios en el Centro de Ingeniería Genética y Biotecnología, Camagüey.</span><span class="en">Network administration, economic-systems support, and user assistance at the Center for Genetic Engineering and Biotechnology, Camagüey.</span></p></article>
      <article><time>1992–1997</time><h3><span class="es">Licenciado en Ciencias de la Computación</span><span class="en">Bachelor in Computer Science</span></h3><p><span class="es">Universidad Central de Las Villas.</span><span class="en">Central University of Las Villas.</span></p></article>
    </div>'''
    src = re.sub(r'    <div class="timeline">.*?\n    </div>', lambda m: tl, src, count=1, flags=re.S)
    # English-first metadata and CV button
    src = src.replace('Sitio académico de Julio Madera: investigación en inteligencia artificial, aprendizaje automático, optimización y algoritmos de estimación de distribuciones.',
                      'Academic website of Julio Madera: research in artificial intelligence, machine learning, optimization and estimation of distribution algorithms.')
    write('index.html', src)

def patch_other_pages():
    for name in ['contact.html', 'research.html', 'projects.html', 'teaching.html']:
        write(name, normalize_shell(open(P(name), encoding='utf-8').read()))
    c = open(P('contact.html'), encoding='utf-8').read()
    c = re.sub(r'<div><a class="button secondary" href="https://github.com/jmadera".*?</div>',
               lambda m: '<div class="button-row"><a class="button secondary" href="https://github.com/jmadera" target="_blank" rel="noopener">GitHub</a>' + profile_buttons() + '</div>', c, count=1, flags=re.S)
    write('contact.html', c)
    for name in ['postgraduate-courses.html', 'responsibilities.html']:
        s = open(P(name), encoding='utf-8').read().replace('\r\n', '\n').replace('<html lang="es">', '<html lang="en">')
        write(name, s)


# ------------------------------------------------------------------ talks / competitions / chart
def build_talks():
    rows = [e for e in EVENTS if e[2].startswith('Julio Madera') and 'Evaluador' not in e[2] and 'Julio Madera Quintana, ' not in e[2][:40]
            and not e[2].startswith('Julio Madera-Quintana, ')]
    def render(r): return f'<li><span class="item-text">{bi(linkify(r[2]), linkify(r[3] or r[2]))}</span></li>'
    main = header('Charlas', 'Talks', 'Charlas y conferencias', 'Talks and lectures',
                  'Conferencias y ponencias presentadas como autor único, del año más reciente al más antiguo.',
                  'Lectures and talks presented as sole author, from the most recent year to the oldest.')
    main += f'\n  <div class="archive-page"><section class="archive-section">\n{year_groups(rows, render)}\n  <div class="button-row"><a class="button secondary" href="events.html">{bi("Todos los eventos", "All events")}</a></div>\n  </section></div>'
    write('talks.html', set_main(base, main, 'Talks | Julio Madera', 'Charlas y conferencias de Julio Madera.', 'talks.html'))
    return len(rows)

def build_competitions():
    res = [(y, es, en) for y, es, en in AWARDS if re.search(r'GECCO|Solar Generation|IEEE', es)]
    res.append((2020, 'Winner Certificate. IEEE World Congress on Computational Intelligence (IEEE WCCI’20), “Evolutionary Computation in the Energy Domain: Smart Grid Applications”. Ansel Y. Rodríguez-González, Bryan Rodrigo Quiroz Palominos, Carlos A. Oliva Moreno, Yoan Martínez-López, Julio Madera.',
                'Winner Certificate. IEEE World Congress on Computational Intelligence (IEEE WCCI’20), “Evolutionary Computation in the Energy Domain: Smart Grid Applications”. Ansel Y. Rodríguez-González, Bryan Rodrigo Quiroz Palominos, Carlos A. Oliva Moreno, Yoan Martínez-López, Julio Madera.'))
    res = sorted(res, key=lambda e: -e[0])
    tasks = []
    for y, t in PUBS:
        if re.search(r'Team|IberLEF|Rest-Mex|HOMO-MEX', t) and re.search(r'ceur-ws|ssrn', t, re.I):
            m = re.search(r'\)\.\s*(.+?)(?:\.\s+(?:CEUR|In\s+Proceedings|Available|Proceedings)|\.\s*https?://|$)', t)
            title = m.group(1).strip().rstrip('.') if m else t[:120]
            title = re.sub(r'\.?\s*In\s+Proceedings.*$', '', title); title = re.sub(r'\s*\((?:July \d+, 2025)\)', '', title)
            url = re.search(r'https?://\S+', t)
            u = url.group(0).rstrip('.,;)') if url else None
            if 'Mexican Sign' in title or 'Team' in title or 'Rest-Mex' in title or 'HOMO' in title.upper() or 'homo-mex' in title.lower() or 'Presta' in title or 'PRESTA' in title:
                tasks.append((y, title, u))
            else:
                tasks.append((y, title, u))
    def r_res(r): return f'<li><span class="item-text">{bi(esc(r[1]), esc(r[2]))}</span></li>'
    def r_task(r):
        link = f' <a href="{r[2]}" target="_blank" rel="noopener">{bi("Ver artículo", "Paper")}</a>' if r[2] else ''
        return f'<li><span class="item-text">{esc(r[1])}.{link}</span></li>'
    main = header('Competencias', 'Competitions', 'Competencias y desafíos', 'Competitions and challenges',
                  'Resultados en competencias internacionales y participación en tareas compartidas (IberLEF, Rest-Mex y otras).',
                  'Results in international competitions and participation in shared tasks (IberLEF, Rest-Mex and others).')
    main += f"""
  <div class="archive-page">
    <section class="archive-section"><h2>{bi('Resultados en competencias de computación evolutiva', 'Evolutionary-computation competition results')}</h2>
{year_groups(res, r_res)}
    </section>
    <section class="archive-section"><h2>{bi('Tareas compartidas (equipo Plenitas y colaboradores)', 'Shared tasks (Plenitas team and collaborators)')}</h2>
      <p>{bi('Participaciones documentadas en informes técnicos y actas (CEUR-WS, SSRN).', 'Participations documented in technical reports and proceedings (CEUR-WS, SSRN).')}</p>
{year_groups(tasks, r_task)}
    </section>
    <div class="button-row"><a class="button secondary" href="awards.html">{bi('Todos los premios', 'All awards')}</a></div>
  </div>"""
    write('competitions.html', set_main(base, main, 'Competitions | Julio Madera', 'Competencias y tareas compartidas en las que participa Julio Madera.', 'competitions.html'))
    return len(res), len(tasks)

TOPICS = [
 ('eda', 'Estimation of distribution algorithms', 'Algoritmos de estimación de distribuciones', r'estimation of distribution|estimación de distribu|\bEDAs?\b|UMDA|distribution algorithm|distribución marginal|MMHC|EDALib|polytree|distribuciones'),
 ('energy', 'Energy and power systems', 'Energía y sistemas eléctricos', r'energ|photovoltaic|solar|smart grid|microred|boiler|steam|distribution networks'),
 ('nlp', 'Text, language and shared tasks', 'Texto, lenguaje y tareas compartidas', r'sentiment|\btext|reviews|rest-mex|homo|hate|opinion|language|humor|irony|translation|headline|emotion|meme|tabular|speech'),
 ('edu', 'Education', 'Educación', r'deserci|dropout|drop out|educaci|académic'),
 ('other', 'Other machine learning and applications', 'Otro aprendizaje automático y aplicaciones', r'.'),
]
def topic_of(t):
    for k, en, es, rx in TOPICS:
        if re.search(rx, t, re.I): return k

def chart_html():
    from collections import Counter, defaultdict
    cnt = defaultdict(Counter)
    for y, t in PUBS: cnt[y][topic_of(t)] += 1
    y0, y1 = min(cnt), max(cnt)
    years = list(range(y0, y1 + 1))
    W, H, ml, mb, mt = 920, 300, 34, 34, 18
    pw = W - ml - 8; ph = H - mb - mt
    mx = max(sum(cnt[y].values()) for y in years)
    step = 5 if mx > 10 else 2
    top = ((mx + step - 1) // step) * step
    bw = pw / len(years)
    g = []
    for v in range(0, top + 1, step):
        yy = mt + ph - ph * v / top
        g.append(f'<line x1="{ml}" x2="{W-8}" y1="{yy:.1f}" y2="{yy:.1f}" class="grid"/><text x="{ml-6}" y="{yy+4:.1f}" class="axis" text-anchor="end">{v}</text>')
    for i, y in enumerate(years):
        x = ml + i * bw + bw * .14; w = bw * .72
        base_y = mt + ph; tot = sum(cnt[y].values())
        for k, *_ in TOPICS:
            n = cnt[y][k]
            if not n: continue
            h = ph * n / top; base_y -= h
            g.append(f'<rect x="{x:.1f}" y="{base_y:.1f}" width="{w:.1f}" height="{max(h-1,0.5):.1f}" class="b-{k}"><title>{y}: {n}</title></rect>')
        if tot: g.append(f'<text x="{x+w/2:.1f}" y="{base_y-4:.1f}" class="tot" text-anchor="middle">{tot}</text>')
        if i % 2 == 0 or len(years) < 14:
            g.append(f'<text x="{x+w/2:.1f}" y="{H-12}" class="axis" text-anchor="middle">{str(y)[2:] if False else y}</text>')
    svg = f'<svg class="pub-chart" viewBox="0 0 {W} {H}" role="img" aria-labelledby="chart-title chart-desc"><title id="chart-title">Publications per year by topic</title><desc id="chart-desc">Stacked bars of publications per year from {y0} to {y1}, grouped by topic.</desc>' + ''.join(g) + '</svg>'
    legend = ''.join(f'<li><span class="sw b-{k}"></span>{bi(es, en)}</li>' for k, en, es, rx in TOPICS)
    rows = ''.join(f'<tr><th scope="row">{y}</th>' + ''.join(f'<td>{cnt[y][k]}</td>' for k, *_ in TOPICS) + f'<td>{sum(cnt[y].values())}</td></tr>' for y in reversed(years) if cnt[y])
    head = ''.join(f'<th scope="col">{bi(es, en)}</th>' for k, en, es, rx in TOPICS)
    return f"""<!--chart-->
      <section class="section" aria-labelledby="pub-activity">
        <div class="section-heading"><p class="eyebrow">{bi('Producción', 'Output')}</p><h2 id="pub-activity">{bi('Publicaciones por año y tema', 'Publications per year and topic')}</h2>
        <p>{bi('Artículos y trabajos en actas del CV. Cada trabajo se asigna a un solo tema según palabras clave del título, por lo que es una aproximación.', 'Articles and conference papers from the CV. Each paper is assigned to one topic using title keywords, so this is an approximation.')}</p></div>
        <figure class="chart-figure">{svg}
        <ul class="chart-legend">{legend}</ul></figure>
        <details class="chart-table"><summary>{bi('Ver datos en tabla', 'View data as table')}</summary>
        <div class="table-wrap"><table><thead><tr><th scope="col">{bi('Año', 'Year')}</th>{head}<th scope="col">Total</th></tr></thead><tbody>{rows}</tbody></table></div></details>
      </section>
      <!--/chart-->
      """

def patch_research():
    src = open(P('research.html'), encoding='utf-8').read()
    src = re.sub(r'<!--chart-->.*?<!--/chart-->\s*', '', src, flags=re.S)
    marker = '<section class="section" aria-labelledby="research-evidence">'
    assert marker in src
    src = src.replace(marker, chart_html() + marker, 1)
    write('research.html', src)

def add_cross_links():
    for name, href, es, en in [('events.html', 'talks.html', 'Charlas y conferencias', 'Talks and lectures'), ('awards.html', 'competitions.html', 'Competencias y desafíos', 'Competitions and challenges')]:
        src = open(P(name), encoding='utf-8').read()
        src = re.sub(r'<div class="button-row cross">.*?</div>\s*', '', src, flags=re.S)
        btn = f'<div class="button-row cross"><a class="button secondary" href="{href}">{bi(es, en)}</a></div>\n  '
        src = src.replace('<div class="archive-page">', '<div class="archive-page">\n  ' + btn, 1)
        write(name, src)

# ------------------------------------------------------------------ PDF
PDF_CSS = '''
@page { size: A4; margin: 16mm 15mm 18mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Liberation Sans", Arial, Helvetica, sans-serif; font-size: 9.6pt; line-height: 1.38; color: #1a1f2b; margin: 0; }
h1 { font-size: 22pt; margin: 0 0 2pt; color: #0e2f58; letter-spacing: -.3pt; }
.sub { font-size: 11pt; color: #3c4a60; margin: 0 0 6pt; }
.contact { font-size: 9pt; color: #3c4a60; border-bottom: 1.5pt solid #123b6d; padding-bottom: 7pt; margin-bottom: 4pt; }
h2 { font-size: 11.5pt; color: #0e2f58; text-transform: uppercase; letter-spacing: .6pt; border-bottom: .6pt solid #b8c6d8; padding-bottom: 2pt; margin: 14pt 0 5pt; break-after: avoid; }
h3 { font-size: 10pt; margin: 8pt 0 2pt; color: #123b6d; break-after: avoid; }
.row { display: grid; grid-template-columns: 24mm 1fr; gap: 0 3mm; margin: 0 0 3.2pt; break-inside: avoid; }
.row .y { font-weight: 700; color: #123b6d; font-size: 9pt; }
.row .t { overflow-wrap: anywhere; }
.row.noyear { grid-template-columns: 1fr; }
a { color: #123b6d; text-decoration: none; }
.note { break-after: avoid; color: #5b687d; font-size: 8.6pt; font-style: italic; margin: 0 0 4pt; }
'''
T = {
 'es': dict(title='Currículum Vitae', role='Profesor Titular · Universidad de Camagüey', degree='Doctor en Ciencias Matemáticas · Licenciado en Ciencias de la Computación',
            nat='Nacionalidad: cubana', addr='Circunvalación Norte km 5½, Camagüey, Cuba, CP 74650', web='Sitio web',
            profile='Perfil', profile_t='Investigación en inteligencia artificial, algoritmos de estimación de distribuciones, aprendizaje automático y optimización.',
            edu='Formación académica', exp='Experiencia profesional', pos='Cargos de dirección', roles='Responsabilidades científicas y servicio editorial',
            pubs='Publicaciones', books='Libros y capítulos de libro', soft='Registros de software', events='Eventos científicos', awards='Premios y reconocimientos',
            phd='Tesis de doctorado tutoradas', ms='Tesis de maestría tutoradas', ms_note='Los títulos se conservan en su idioma original.',
            teach='Cursos de postgrado impartidos', train='Postgrados y cursos recibidos', lang='Idiomas', present='actual', nd='s/f',
            scopus_note='(Scopus) indica indexación en Scopus según el currículo. Orden: del más reciente al más antiguo.'),
 'en': dict(title='Curriculum Vitae', role='Full Professor · University of Camagüey', degree='Doctor of Mathematical Sciences · Bachelor in Computer Science',
            nat='Nationality: Cuban', addr='Circunvalación Norte km 5½, Camagüey, Cuba, ZIP 74650', web='Website',
            profile='Profile', profile_t='Research in artificial intelligence, estimation of distribution algorithms, machine learning and optimization.',
            edu='Education', exp='Professional experience', pos='Management positions', roles='Scientific responsibilities and editorial service',
            pubs='Publications', books='Books and book chapters', soft='Software registrations', events='Scientific events', awards='Awards and recognitions',
            phd='Doctoral theses supervised', ms='Master’s theses supervised', ms_note='Titles are kept in their original language (Spanish).',
            teach='Postgraduate courses taught', train='Postgraduate training received', lang='Languages', present='present', nd='n.d.',
            scopus_note='(Scopus) marks Scopus-indexed items as stated in the source CV. Order: newest to oldest.'),
}

def pdf_html(lg):
    t = T[lg]; ix = 0 if lg == 'es' else 1
    def pick(es, en): return es if lg == 'es' else en
    def row(y, text, raw=False):
        body = text if raw else esc(text)
        return f'<div class="row"><div class="y">{y}</div><div class="t">{body}</div></div>'
    def plain(text): return f'<div class="row noyear"><div class="t">{linkify(text)}</div></div>'
    o = [f'<h1>{esc(D.NAME_FULL)}</h1><p class="sub">{t["role"]}<br>{t["degree"]}</p>',
         f'<div class="contact">{D.EMAIL} · jmadera.github.io · {t["nat"]}<br>ORCID: <a href="{ORCID}">{ORCID[8:]}</a> · Google Scholar: <a href="{SCHOLAR_ES}">cGe6Tv0AAAAJ</a><br>{t["addr"]}</div>',
         f'<h2>{t["profile"]}</h2><p style="margin:0">{t["profile_t"]}</p>']
    o.append(f'<h2>{t["edu"]}</h2>')
    for a, b, es, en, ies, ien in D.EDUCATION:
        o.append(row(f'{a}–{b}', f'<b>{pick(es, en)}</b> — {pick(ies, ien)}', True))
    o.append(f'<h2>{t["exp"]}</h2>')
    for p, es, en, pes, pen in D.EXPERIENCE:
        p = p.strip(); p = p + ' ' + t['present'] if p.endswith('–') else p
        o.append(row(p.replace(' – ', '–').replace('– ', '–'), f'<b>{pick(es, en)}</b> — {pick(pes, pen)}', True))
    o.append(f'<h2>{t["pos"]}</h2>')
    for s, e, es, en in D.POSITIONS:
        o.append(row(f'{s}–{e if e else t["present"]}', pick(es, en)))
    o.append(f'<h2>{t["roles"]}</h2>')
    for es, en in D.ROLES: o.append(plain(pick(es, en)))
    o.append(f'<h2>{t["pubs"]}</h2><p class="note">{t["scopus_note"]}</p>')
    for y, tx in PUBS: o.append(row(y or t['nd'], linkify(tx), True))
    o.append(f'<h2>{t["books"]}</h2>')
    for y, tx in BOOKS: o.append(row(y or t['nd'], linkify(tx), True))
    o.append(f'<h2>{t["soft"]}</h2>')
    for y, tx in SOFT: o.append(row(y or t['nd'], linkify(tx), True))
    o.append(f'<h2>{t["events"]}</h2>')
    for y, m, es, en in EVENTS: o.append(row(y, linkify(pick(es, en or es)), True))
    o.append(f'<h2>{t["awards"]}</h2>')
    for y, es, en in AWARDS: o.append(row(y, pick(es, en)))
    o.append(f'<h2>{t["phd"]}</h2>')
    for y, es, en in PHD: o.append(row(y, pick(es, en)))
    o.append(f'<h2>{t["ms"]}</h2><p class="note">{t["ms_note"]}</p>')
    for y, tx in MASTERS: o.append(row(y, tx))
    o.append(f'<h2>{t["teach"]}</h2>')
    for es, en in COURSES:
        tx = pick(es, en); m = re.search(r'\((\d{4})\)', tx) or re.search(r'\b(19|20)\d{2}\b', tx)
        y = m.group(1) if m and len(m.group(1)) == 4 else (m.group(0) if m else '')
        o.append(row(y, tx))
    o.append(f'<h2>{t["train"]}</h2>')
    for y, es, en, ies, ien in TRAINING: o.append(row(y, f'<b>{esc(pick(es, en))}</b> — {esc(pick(ies, ien))}', True))
    o.append(f'<h2>{t["lang"]}</h2>')
    for a, b, c, d in D.LANGUAGES: o.append(plain(f'{pick(a, b)} — {pick(c, d)}'))
    return f'<!doctype html><html lang="{lg}"><head><meta charset="utf-8"><title>{t["title"]} — {D.NAME}</title><style>{PDF_CSS}</style></head><body>' + '\n'.join(o) + '</body></html>'

def build_pdfs():
    os.makedirs(P('files'), exist_ok=True)
    tmp = tempfile.mkdtemp()
    for lg in ('en', 'es'):
        hp = os.path.join(tmp, f'cv_{lg}.html')
        open(hp, 'w', encoding='utf-8').write(pdf_html(lg))
        out = P('files', f'julio_madera_{lg}.pdf')
        subprocess.run(['google-chrome', '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                        f'--print-to-pdf={out}', 'file://' + hp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print('PDF', out, os.path.getsize(out))

if __name__ == '__main__':
    build_publications(); build_events(); build_supervision(); build_awards(); build_leadership(); build_cv(); build_index(); patch_other_pages(); print('talks', build_talks(), 'comp', build_competitions()); patch_research(); add_cross_links()
    print('pubs', len(PUBS), 'books', len(BOOKS), 'soft', len(SOFT), 'events', len(EVENTS), 'awards', len(AWARDS))
    missing = [t for y, t in PUBS if not y]
    print('pubs sin año:', missing)
    import seo; seo.run()
    if '--no-pdf' not in sys.argv: build_pdfs()

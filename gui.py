import tkinter as tk
from tkinter import ttk, font as tkfont, messagebox
import threading
import random
import time
import math
import os

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# color palette for the dark theme
BG      = '#0d1117'
PANEL   = '#161b22'
BORDER  = '#30363d'
ACCENT  = '#58a6ff'
ACCENT2 = '#f78166'
ACCENT3 = '#3fb950'
MUTED   = '#8b949e'
WHITE   = '#e6edf3'
GOLD    = '#d29922'

# one color per student for the schedule grid
STUDENT_COLORS = {
    'S1': '#58a6ff',
    'S2': '#f78166',
    'S3': '#3fb950',
    'S4': '#d29922',
    'S5': '#a371f7',
}

DAYS  = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
TIMES = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
TIME_LABELS = {
    8: '8AM', 9: '9AM', 10: '10AM', 11: '11AM', 12: '12PM',
    13: '1PM', 14: '2PM', 15: '3PM', 16: '4PM', 17: '5PM'
}


class GASchedulerGUI:
    def __init__(self, root, students, courses, friend_pairs, config):
        self.root         = root
        self.students     = students
        self.courses      = courses
        self.friend_pairs = friend_pairs
        self.config       = config

        self.best_result  = None
        self.all_results  = []
        self.running      = False
        self._gen_history = []

        root.title('GA Course Scheduler  —  AI2002 Assignment 02')
        root.configure(bg=BG)
        root.geometry('1400x880')
        root.minsize(1100, 700)

        self._setup_fonts()
        self._build_ui()

    # sets up all fonts used across the GUI
    def _setup_fonts(self):
        self.font_h1    = tkfont.Font(family='Courier', size=18, weight='bold')
        self.font_h2    = tkfont.Font(family='Courier', size=12, weight='bold')
        self.font_body  = tkfont.Font(family='Courier', size=10)
        self.font_small = tkfont.Font(family='Courier', size=9)
        self.font_mono  = tkfont.Font(family='Courier', size=9)
        self.font_label = tkfont.Font(family='Courier', size=8)

    def _build_ui(self):
        # top bar with title
        topbar = tk.Frame(self.root, bg=PANEL, height=52)
        topbar.pack(fill='x', side='top')
        tk.Label(topbar, text='◈  GENETIC ALGORITHM  ·  COURSE SCHEDULER',
                 font=self.font_h1, fg=ACCENT, bg=PANEL, pady=10).pack(side='left', padx=20)
        tk.Label(topbar, text='AI2002 – Spring 2026',
                 font=self.font_body, fg=MUTED, bg=PANEL).pack(side='right', padx=20, pady=14)

        # style the notebook tabs
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TNotebook', background=BG, borderwidth=0)
        style.configure('Dark.TNotebook.Tab', background=PANEL, foreground=MUTED,
                        font=('Courier', 10, 'bold'), padding=[16, 8], borderwidth=0)
        style.map('Dark.TNotebook.Tab',
                  background=[('selected', BG)],
                  foreground=[('selected', ACCENT)])

        nb = ttk.Notebook(self.root, style='Dark.TNotebook')
        nb.pack(fill='both', expand=True, padx=0, pady=0)

        # create 4 tabs
        self.tab_run     = self._make_tab(nb, '  ▶  RUN GA  ')
        self.tab_sched   = self._make_tab(nb, '  ▦  SCHEDULE  ')
        self.tab_charts  = self._make_tab(nb, '  ◈  CHARTS  ')
        self.tab_fitness = self._make_tab(nb, '  ▩  FITNESS  ')

        nb.add(self.tab_run,     text='  ▶  RUN GA  ')
        nb.add(self.tab_sched,   text='  ▦  SCHEDULE  ')
        nb.add(self.tab_charts,  text='  ◈  CHARTS  ')
        nb.add(self.tab_fitness, text='  ▩  FITNESS  ')

        self._build_run_tab()
        self._build_schedule_tab()
        self._build_charts_tab()
        self._build_fitness_tab()

    # returns a blank dark frame for a tab
    def _make_tab(self, nb, name):
        f = tk.Frame(nb, bg=BG)
        return f

    def _build_run_tab(self):
        p = self.tab_run

        # left side: parameter controls
        ctrl = tk.Frame(p, bg=PANEL, width=280)
        ctrl.pack(side='left', fill='y', padx=0, pady=0)
        ctrl.pack_propagate(False)

        self._section_label(ctrl, 'PARAMETERS')
        self._param_row(ctrl, 'Population size', 'pop_size',  60)
        self._param_row(ctrl, 'Max generations', 'max_gens',  300)
        self._param_row(ctrl, 'Number of runs',  'num_runs',  10)
        self._param_row(ctrl, 'Random seed',     'seed',      42)
        self._param_row(ctrl, 'Crossover prob',  'cx_prob',   0.80)
        self._param_row(ctrl, 'Tournament size', 'tour_size', 5)

        tk.Frame(ctrl, bg=BORDER, height=1).pack(fill='x', padx=12, pady=10)

        self._section_label(ctrl, 'MUTATION RATES')
        self._param_row(ctrl, 'Section change', 'mr_sec',    0.12)
        self._param_row(ctrl, 'Course swap',    'mr_swap',   0.10)
        self._param_row(ctrl, 'Time shift',     'mr_time',   0.08)
        self._param_row(ctrl, 'Friend align',   'mr_friend', 0.15)

        tk.Frame(ctrl, bg=BORDER, height=1).pack(fill='x', padx=12, pady=10)

        # start and stop buttons
        btn = tk.Button(ctrl, text='▶  START GA', font=self.font_h2,
                        bg=ACCENT, fg=BG, relief='flat', cursor='hand2',
                        activebackground=ACCENT2, activeforeground=BG,
                        command=self._start_ga, pady=10)
        btn.pack(fill='x', padx=16, pady=4)

        btn2 = tk.Button(ctrl, text='⬛  STOP', font=self.font_body,
                         bg=PANEL, fg=ACCENT2, relief='flat', cursor='hand2',
                         highlightbackground=ACCENT2, highlightthickness=1,
                         command=self._stop_ga, pady=8)
        btn2.pack(fill='x', padx=16, pady=4)

        # right side: live output area
        right = tk.Frame(p, bg=BG)
        right.pack(side='left', fill='both', expand=True, padx=0)

        self._section_label(right, 'LIVE OUTPUT', padx=20)

        # status labels row
        prog_frame = tk.Frame(right, bg=BG)
        prog_frame.pack(fill='x', padx=20, pady=(0, 8))

        self.gen_var    = tk.StringVar(value='Gen: —')
        self.fit_var    = tk.StringVar(value='Best: —')
        self.run_var    = tk.StringVar(value='Run: —')
        self.status_var = tk.StringVar(value='Idle')

        info_row = tk.Frame(prog_frame, bg=BG)
        info_row.pack(fill='x')
        for var, col in [(self.run_var, ACCENT), (self.gen_var, ACCENT3),
                         (self.fit_var, GOLD), (self.status_var, ACCENT2)]:
            tk.Label(info_row, textvariable=var, font=self.font_body,
                     fg=col, bg=BG, padx=14).pack(side='left')

        # canvas for the live fitness chart
        self.live_canvas = tk.Canvas(right, bg=PANEL, height=220,
                                     highlightthickness=1, highlightbackground=BORDER)
        self.live_canvas.pack(fill='x', padx=20, pady=(0, 8))
        self._draw_live_axes()

        # scrollable log text box
        log_frame = tk.Frame(right, bg=BG)
        log_frame.pack(fill='both', expand=True, padx=20, pady=(0, 12))
        tk.Label(log_frame, text='LOG', font=self.font_label, fg=MUTED, bg=BG).pack(anchor='w')
        sb = tk.Scrollbar(log_frame)
        sb.pack(side='right', fill='y')
        self.log_box = tk.Text(log_frame, bg=PANEL, fg=WHITE, font=self.font_mono,
                               relief='flat', yscrollcommand=sb.set,
                               state='disabled', wrap='none',
                               highlightthickness=1, highlightbackground=BORDER)
        self.log_box.pack(fill='both', expand=True)
        sb.config(command=self.log_box.yview)

        # color tags for different log message types
        self.log_box.tag_config('good', foreground=ACCENT3)
        self.log_box.tag_config('warn', foreground=GOLD)
        self.log_box.tag_config('err',  foreground=ACCENT2)
        self.log_box.tag_config('head', foreground=ACCENT)

    # adds a label + entry field row to a panel, stores the var in self._params
    def _param_row(self, parent, label, key, default):
        if not hasattr(self, '_params'):
            self._params = {}
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill='x', padx=14, pady=2)
        tk.Label(row, text=label, font=self.font_small, fg=MUTED,
                 bg=PANEL, width=17, anchor='w').pack(side='left')
        var = tk.StringVar(value=str(default))
        self._params[key] = var
        ent = tk.Entry(row, textvariable=var, font=self.font_small,
                       bg=BG, fg=WHITE, relief='flat', width=8,
                       insertbackground=ACCENT,
                       highlightthickness=1, highlightbackground=BORDER)
        ent.pack(side='right')

    # adds a section heading label to a panel
    def _section_label(self, parent, text, padx=14):
        tk.Label(parent, text=text, font=self.font_label, fg=ACCENT,
                 bg=PANEL if parent != self.tab_run else parent.cget('bg'),
                 pady=6, padx=padx, anchor='w').pack(fill='x')

    # draws the empty axes for the live chart
    def _draw_live_axes(self):
        c = self.live_canvas
        c.delete('all')
        W = c.winfo_reqwidth() or 800
        H = 220
        pad = 40
        c.create_line(pad, H - pad, W - 10, H - pad, fill=BORDER)
        c.create_line(pad, 10, pad, H - pad, fill=BORDER)
        c.create_text(pad - 4, 10, text='fit', fill=MUTED, font=self.font_label, anchor='e')
        c.create_text(W // 2, H - 6, text='generation', fill=MUTED, font=self.font_label)

    # redraws the live chart with current best and avg fitness history
    def _update_live_chart(self, best_hist, avg_hist):
        c = self.live_canvas
        c.delete('all')
        c.update_idletasks()
        W = c.winfo_width() or 800
        H = 220
        pad = 45

        if not best_hist:
            return

        # find the y range for scaling
        mn = min(min(best_hist), min(avg_hist)) if avg_hist else min(best_hist)
        mx = max(max(best_hist), max(avg_hist)) if avg_hist else max(best_hist)
        rng = mx - mn if mx != mn else 1

        # converts a (index, value) pair to canvas (x, y)
        def to_xy(i, v):
            x = pad + (i / max(len(best_hist) - 1, 1)) * (W - pad - 10)
            y = (H - pad) - ((v - mn) / rng) * (H - pad - 10)
            return x, y

        # draw horizontal grid lines
        for k in range(5):
            y = (H - pad) - k * (H - pad - 10) / 4
            v = mn + k * rng / 4
            c.create_line(pad, y, W - 10, y, fill=BORDER, dash=(2, 4))
            c.create_text(pad - 4, y, text=f'{v:.2f}', fill=MUTED,
                          font=self.font_label, anchor='e')

        # draw avg line in muted color
        if avg_hist:
            pts = [to_xy(i, v) for i, v in enumerate(avg_hist)]
            flat = []
            for xy in pts:
                flat.append(xy[0])
                flat.append(xy[1])
            if len(flat) >= 4:
                c.create_line(*flat, fill=MUTED, width=1, smooth=True)

        # draw best line in green
        pts = [to_xy(i, v) for i, v in enumerate(best_hist)]
        flat = []
        for xy in pts:
            flat.append(xy[0])
            flat.append(xy[1])
        if len(flat) >= 4:
            c.create_line(*flat, fill=ACCENT3, width=2, smooth=True)

        # dot and label at the last point
        lx, ly = pts[-1]
        c.create_oval(lx - 4, ly - 4, lx + 4, ly + 4, fill=ACCENT3, outline='')
        c.create_text(lx + 6, ly, text=f'{best_hist[-1]:.3f}',
                      fill=ACCENT3, font=self.font_label, anchor='w')

        c.create_text(pad, 8, text='■ best', fill=ACCENT3, font=self.font_label, anchor='w')
        c.create_text(pad + 60, 8, text='■ avg', fill=MUTED, font=self.font_label, anchor='w')

    # reads params and starts the GA thread
    def _start_ga(self):
        if self.running:
            return
        self.running = True
        self._gen_history = []
        self._log_clear()

        # apply user-entered parameters to config
        p = self._params
        self.config['population']['size'] = int(p['pop_size'].get())
        self.config['termination']['max_generations'] = int(p['max_gens'].get())
        self.config['crossover']['probability'] = float(p['cx_prob'].get())
        self.config['selection']['tournament']['tournament_size'] = int(p['tour_size'].get())
        self.config['mutation']['base_rates']['section_change'] = float(p['mr_sec'].get())
        self.config['mutation']['base_rates']['course_swap']    = float(p['mr_swap'].get())
        self.config['mutation']['base_rates']['time_shift']     = float(p['mr_time'].get())
        self.config['mutation']['base_rates']['friend_align']   = float(p['mr_friend'].get())

        n_runs = int(p['num_runs'].get())
        seed   = int(p['seed'].get())
        seeds  = [seed + i * 13 for i in range(n_runs)]

        self._log('=' * 52, 'head')
        self._log(f'  Starting {n_runs} GA runs  (base seed={seed})', 'head')
        self._log('=' * 52, 'head')

        # run GA in background thread so GUI stays responsive
        t = threading.Thread(target=self._ga_thread, args=(seeds,), daemon=True)
        t.start()

    def _stop_ga(self):
        self.running = False
        self._log('[STOPPED by user]', 'err')
        self.status_var.set('Stopped')

    # runs each seed sequentially in the background thread
    def _ga_thread(self, seeds):
        from main import run_ga

        all_results = []
        for i, seed in enumerate(seeds):
            if not self.running:
                break

            # update status labels on the main thread
            self.root.after(0, lambda i=i, s=seed: (
                self.run_var.set(f'Run: {i+1}/{len(seeds)}'),
                self.status_var.set('Running…')
            ))
            self._log(f'\n── Run {i+1}  seed={seed} ──', 'head')

            res = self._run_with_callback(seed, i + 1)
            if res:
                all_results.append(res)
                best = res['best']['fitness']
                self._log(f'  ✓ Best fitness: {best:.4f}  (conv gen {res["conv_gen"]})', 'good')
            else:
                self._log(f'  ✗ Run failed', 'err')

        if all_results:
            self.all_results = all_results
            self.best_result = max(all_results, key=lambda r: r['best']['fitness'])
            self.root.after(0, self._on_runs_complete)

        self.running = False
        self.root.after(0, lambda: self.status_var.set('Done ✓'))

    # runs the GA loop manually so we can push live updates to the GUI
    def _run_with_callback(self, seed, run_id):
        from utils import _default_config, load_courses, load_students, population_diversity
        from chromosome import initialise_population
        from fitness import evaluate_population
        from selection import select_parents, apply_elitism, inject_random_individuals
        from operators import crossover, mutate, get_adaptive_rates
        import time as tmod

        students     = self.students
        courses      = self.courses
        friend_pairs = self.friend_pairs
        config       = self.config
        random.seed(seed)

        pop_size   = config['population']['size']
        base_rates = dict(config['mutation']['base_rates'])
        div_cfg    = config['diversity']['maintenance']
        check_int  = config['mutation']['adaptive']['check_interval']

        population = initialise_population(pop_size, students, courses, config)
        evaluate_population(population, students, courses, friend_pairs, config)

        best_hist  = []
        avg_hist   = []
        worst_hist = []
        div_hist   = []
        current_rates = dict(base_rates)
        conv_gen = None
        start = tmod.time()

        max_gens = config['termination']['max_generations']

        for gen in range(max_gens):
            if not self.running:
                break

            # check diversity every N generations and adapt mutation rates
            if gen % check_int == 0:
                div = population_diversity(population)
                div_hist.append(div)
                if config['mutation']['adaptive']['enabled']:
                    current_rates = get_adaptive_rates(base_rates, div, config)
                if div_cfg['enabled'] and div < div_cfg['low_threshold']:
                    n_inj = int(pop_size * div_cfg['injection_rate'])
                    population = inject_random_individuals(population, n_inj, students, courses, config)
                    evaluate_population(population, students, courses, friend_pairs, config)
            else:
                div = div_hist[-1] if div_hist else 1.0

            # build the next generation
            new_pop = []
            while len(new_pop) < pop_size:
                p1, p2 = select_parents(population, config)
                c1c, c2c = crossover(p1, p2, students, courses, config)
                c1 = mutate({'chromosome': c1c, 'fitness': None}, students, courses, config, friend_pairs, current_rates)
                c2 = mutate({'chromosome': c2c, 'fitness': None}, students, courses, config, friend_pairs, current_rates)
                new_pop.extend([c1, c2])

            new_pop = new_pop[:pop_size]
            evaluate_population(new_pop, students, courses, friend_pairs, config)
            new_pop = apply_elitism(population, new_pop, config)
            population = new_pop

            # record stats for this generation
            fits    = [ind['fitness'] for ind in population]
            best_f  = max(fits)
            avg_f   = sum(fits) / len(fits)
            worst_f = min(fits)
            best_hist.append(best_f)
            avg_hist.append(avg_f)
            worst_hist.append(worst_f)

            # push chart update to GUI every 5 generations
            if gen % 5 == 0:
                bh = list(best_hist)
                ah = list(avg_hist)
                gn = gen
                bf = best_f
                self.root.after(0, lambda bh=bh, ah=ah, gn=gn, bf=bf: (
                    self._update_live_chart(bh, ah),
                    self.gen_var.set(f'Gen: {gn}'),
                    self.fit_var.set(f'Best: {bf:.4f}')
                ))

            from main import should_terminate
            stop, reason = should_terminate(gen + 1, best_hist, population, config)
            if stop:
                conv_gen = gen + 1
                self._log(f'  [stop gen {conv_gen}] {reason}', 'warn')
                break

        elapsed  = tmod.time() - start
        best_ind = max(population, key=lambda i: i['fitness'])

        return {
            'best':         best_ind,
            'best_history': best_hist,
            'avg_history':  avg_hist,
            'worst_history':worst_hist,
            'div_history':  div_hist,
            'conv_gen':     conv_gen or len(best_hist),
            'elapsed':      elapsed,
            'run_id':       run_id,
            'seed':         seed,
        }

    # called on main thread when all runs are done
    def _on_runs_complete(self):
        self._log('\n' + '=' * 52, 'head')
        self._log('  ALL RUNS COMPLETE', 'good')
        fits = [r['best']['fitness'] for r in self.all_results]
        self._log(f'  Best:  {max(fits):.4f}', 'good')
        self._log(f'  Avg:   {sum(fits)/len(fits):.4f}', 'good')
        self._log('=' * 52, 'head')

        # refresh all the other tabs with the new results
        self._refresh_schedule_tab()
        self._refresh_charts_tab()
        self._refresh_fitness_tab()

        messagebox.showinfo('GA Complete',
            f'All runs finished!\nBest fitness: {max(fits):.4f}\n'
            f'Check Schedule / Charts / Fitness tabs.')

    # appends a message to the log box with optional color tag
    def _log(self, msg, tag=None):
        def _do():
            self.log_box.config(state='normal')
            if tag:
                self.log_box.insert('end', msg + '\n', tag)
            else:
                self.log_box.insert('end', msg + '\n')
            self.log_box.see('end')
            self.log_box.config(state='disabled')
        self.root.after(0, _do)

    def _log_clear(self):
        self.log_box.config(state='normal')
        self.log_box.delete('1.0', 'end')
        self.log_box.config(state='disabled')

    def _build_schedule_tab(self):
        p = self.tab_sched

        # legend bar showing which color = which student
        leg = tk.Frame(p, bg=PANEL)
        leg.pack(fill='x', padx=20, pady=(12, 4))
        tk.Label(leg, text='WEEKLY TIMETABLE', font=self.font_h2,
                 fg=ACCENT, bg=PANEL, padx=12, pady=6).pack(side='left')
        for sid, col in STUDENT_COLORS.items():
            tk.Label(leg, text=f'  ■ {sid}  ', font=self.font_small,
                     fg=col, bg=PANEL, cursor='arrow').pack(side='left', padx=4)

        self.sched_note = tk.Label(p, text='Run the GA to see the schedule.',
                                   font=self.font_body, fg=MUTED, bg=BG)
        self.sched_note.pack(pady=30)

        self.sched_frame = tk.Frame(p, bg=BG)

    def _refresh_schedule_tab(self):
        if not self.best_result:
            return
        self.sched_note.pack_forget()

        # clear old grid if re-running
        for w in self.sched_frame.winfo_children():
            w.destroy()
        self.sched_frame.pack(fill='both', expand=True, padx=20, pady=8)

        chromosome = self.best_result['best']['chromosome']
        self._draw_grid(self.sched_frame, chromosome)
        self._draw_friend_panel(self.sched_frame, chromosome)

    def _draw_grid(self, parent, chromosome):
        # build a lookup: (day, time) -> list of (student_id, course_id)
        lookup = {}
        for sid, entries in chromosome.items():
            for entry in entries:
                for (d, t) in entry['days_times']:
                    key = (d, t)
                    if key not in lookup:
                        lookup[key] = []
                    lookup[key].append((sid, entry['course_id']))

        canvas_frame = tk.Frame(parent, bg=BG)
        canvas_frame.pack(fill='both', expand=True)

        # column headers (day names)
        hdr = tk.Frame(canvas_frame, bg=BG)
        hdr.pack(fill='x')
        tk.Label(hdr, text='', width=7, bg=BG).pack(side='left')
        for day in DAYS:
            tk.Label(hdr, text=day[:3].upper(), font=self.font_h2, fg=ACCENT,
                     bg=PANEL, width=18, relief='flat',
                     highlightthickness=1, highlightbackground=BORDER,
                     pady=6).pack(side='left', padx=1, pady=1)

        # one row per time slot
        for t in TIMES:
            row = tk.Frame(canvas_frame, bg=BG)
            row.pack(fill='x', pady=1)
            tk.Label(row, text=TIME_LABELS[t], font=self.font_small,
                     fg=MUTED, bg=BG, width=7, anchor='e').pack(side='left')

            for day in DAYS:
                items = lookup.get((day, t), [])
                if items:
                    cell_bg = STUDENT_COLORS.get(items[0][0], ACCENT)
                    lines = []
                    for sid, cid in items[:3]:
                        lines.append(f"{sid}: {cid}")
                    text = '\n'.join(lines)
                    if len(items) > 3:
                        text += f'\n+{len(items)-3} more'
                    cell = tk.Label(row, text=text, font=self.font_label,
                                    fg=BG, bg=cell_bg, width=18,
                                    relief='flat', pady=2,
                                    highlightthickness=1, highlightbackground=BG)
                else:
                    cell = tk.Label(row, text='', bg=PANEL, width=18,
                                    relief='flat', pady=2,
                                    highlightthickness=1, highlightbackground=BORDER)
                cell.pack(side='left', padx=1)

    # shows which friends share which classes
    def _draw_friend_panel(self, parent, chromosome):
        fp = tk.Frame(parent, bg=PANEL, bd=0)
        fp.pack(fill='x', pady=(10, 0))
        tk.Label(fp, text='FRIEND OVERLAPS', font=self.font_h2, fg=GOLD,
                 bg=PANEL, padx=12, pady=6).pack(anchor='w')

        for pair in self.friend_pairs:
            sa, sb = pair[0], pair[1]

            # build section sets for each student
            ea = set()
            for e in chromosome.get(sa, []):
                ea.add((e['course_id'], e['section_id']))
            eb = set()
            for e in chromosome.get(sb, []):
                eb.add((e['course_id'], e['section_id']))

            shared = ea & eb
            count  = len(shared)
            col    = ACCENT3 if count > 0 else MUTED

            name_parts = []
            for c, s in sorted(shared):
                name_parts.append(f"{c}§{s}")
            names = ', '.join(name_parts) if name_parts else 'none'

            row_txt = f"  {sa} ↔ {sb}:  {count} shared  [{names}]"
            tk.Label(fp, text=row_txt, font=self.font_small, fg=col,
                     bg=PANEL, pady=2).pack(anchor='w', padx=12)

    def _build_charts_tab(self):
        p = self.tab_charts
        self.charts_note = tk.Label(p, text='Run the GA to see convergence charts.',
                                    font=self.font_body, fg=MUTED, bg=BG)
        self.charts_note.pack(pady=40)
        self.charts_canvas_frame = tk.Frame(p, bg=BG)

    # draws convergence and diversity plots using matplotlib
    def _refresh_charts_tab(self):
        if not self.all_results or not HAS_MPL:
            return
        self.charts_note.pack_forget()
        for w in self.charts_canvas_frame.winfo_children():
            w.destroy()
        self.charts_canvas_frame.pack(fill='both', expand=True)

        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        fig.patch.set_facecolor(BG)

        colors = ['#58a6ff', '#f78166', '#3fb950', '#d29922', '#a371f7',
                  '#79c0ff', '#ffa657', '#56d364', '#e3b341', '#d2a8ff']

        # left chart: convergence (best/avg/worst per run)
        ax1 = axes[0]
        ax1.set_facecolor(PANEL)
        for i, r in enumerate(self.all_results):
            col = colors[i % len(colors)]
            ax1.plot(r['best_history'],  color=col, linewidth=1.5, label=f"Run {r['run_id']}", alpha=0.85)
            ax1.plot(r['avg_history'],   color=col, linewidth=0.7, linestyle='--', alpha=0.35)
            ax1.plot(r['worst_history'], color=col, linewidth=0.5, linestyle=':', alpha=0.2)
        ax1.set_title('Convergence – Best/Avg/Worst', color=WHITE, fontsize=11)
        ax1.set_xlabel('Generation', color=MUTED)
        ax1.set_ylabel('Fitness', color=MUTED)
        ax1.tick_params(colors=MUTED)
        ax1.legend(fontsize=7, ncol=2, facecolor=PANEL, labelcolor=WHITE)
        for sp in ax1.spines.values():
            sp.set_color(BORDER)
        ax1.grid(alpha=0.15, color=BORDER)

        # right chart: diversity over generations
        ax2 = axes[1]
        ax2.set_facecolor(PANEL)
        for i, r in enumerate(self.all_results):
            if r['div_history']:
                gens = [g * 10 for g in range(len(r['div_history']))]
                ax2.plot(gens, r['div_history'], color=colors[i % len(colors)],
                         linewidth=1.4, label=f"Run {r['run_id']}", alpha=0.85,
                         marker='o', markersize=3)
        ax2.axhline(0.30, color=ACCENT2, linestyle='--', linewidth=1.5, label='30% threshold')
        ax2.set_title('Population Diversity', color=WHITE, fontsize=11)
        ax2.set_xlabel('Generation', color=MUTED)
        ax2.set_ylabel('Diversity (unique fraction)', color=MUTED)
        ax2.tick_params(colors=MUTED)
        ax2.set_ylim(0, 1.05)
        ax2.legend(fontsize=7, facecolor=PANEL, labelcolor=WHITE)
        for sp in ax2.spines.values():
            sp.set_color(BORDER)
        ax2.grid(alpha=0.15, color=BORDER)

        plt.tight_layout(pad=1.5)
        canvas = FigureCanvasTkAgg(fig, master=self.charts_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=12, pady=12)

    def _build_fitness_tab(self):
        p = self.tab_fitness
        self.fit_note = tk.Label(p, text='Run the GA to see fitness breakdown.',
                                 font=self.font_body, fg=MUTED, bg=BG)
        self.fit_note.pack(pady=40)
        self.fit_inner = tk.Frame(p, bg=BG)

    # builds per-student fitness cards and the multi-run bar chart
    def _refresh_fitness_tab(self):
        if not self.best_result:
            return
        self.fit_note.pack_forget()
        for w in self.fit_inner.winfo_children():
            w.destroy()
        self.fit_inner.pack(fill='both', expand=True, padx=20, pady=12)

        best = self.best_result['best']
        bd   = best.get('breakdown', {})

        # top summary bar
        top = tk.Frame(self.fit_inner, bg=PANEL)
        top.pack(fill='x', pady=(0, 10))
        tk.Label(top, text=f'  BEST FITNESS: {best["fitness"]:.4f}',
                 font=self.font_h2, fg=ACCENT3, bg=PANEL, pady=8).pack(side='left')
        tk.Label(top, text=f'Run {self.best_result["run_id"]}  seed={self.best_result["seed"]}  '
                            f'conv gen={self.best_result["conv_gen"]}',
                 font=self.font_small, fg=MUTED, bg=PANEL).pack(side='right', padx=12)

        cards = tk.Frame(self.fit_inner, bg=BG)
        cards.pack(fill='both', expand=True)

        components  = ['time', 'gap', 'friend', 'workload', 'lunch']
        comp_labels = {'time': 'Time Pref', 'gap': 'Gap Min', 'friend': 'Friend Sat',
                       'workload': 'Workload', 'lunch': 'Lunch Break'}
        comp_colors = {'time': ACCENT, 'gap': ACCENT3, 'friend': GOLD,
                       'workload': ACCENT2, 'lunch': '#a371f7'}

        # one card per student
        for col_idx, (sid, data) in enumerate(bd.items()):
            s_col = STUDENT_COLORS.get(sid, ACCENT)
            card  = tk.Frame(cards, bg=PANEL, bd=0,
                             highlightthickness=1, highlightbackground=s_col)
            card.grid(row=0, column=col_idx, padx=6, pady=6, sticky='nsew')
            cards.grid_columnconfigure(col_idx, weight=1)

            tk.Label(card, text=sid, font=self.font_h2, fg=s_col, bg=PANEL, pady=6).pack()
            tk.Label(card, text=self.students[sid]['name'], font=self.font_small,
                     fg=MUTED, bg=PANEL).pack()
            tk.Frame(card, bg=s_col, height=2).pack(fill='x', padx=8)

            # mini progress bar for each fitness component
            for comp in components:
                val = data.get(comp, 0)
                row = tk.Frame(card, bg=PANEL)
                row.pack(fill='x', padx=10, pady=2)
                tk.Label(row, text=comp_labels[comp], font=self.font_label,
                         fg=MUTED, bg=PANEL, width=11, anchor='w').pack(side='left')
                bar_bg = tk.Frame(row, bg=BORDER, height=12, width=80)
                bar_bg.pack(side='left', padx=4)
                bar_bg.pack_propagate(False)
                filled_w = max(1, int(val * 80))
                bar_fg = tk.Frame(bar_bg, bg=comp_colors[comp], height=12, width=filled_w)
                bar_fg.place(x=0, y=0)
                tk.Label(row, text=f'{val:.2f}', font=self.font_label,
                         fg=comp_colors[comp], bg=PANEL, width=5).pack(side='left')

            penalty = data.get('penalty', 0)
            p_col = ACCENT3 if penalty == 0 else ACCENT2
            tk.Label(card, text=f'Penalty: {penalty}', font=self.font_small,
                     fg=p_col, bg=PANEL, pady=4).pack()
            tk.Label(card, text=f'Total:  {data.get("total", 0):.4f}', font=self.font_body,
                     fg=WHITE, bg=PANEL, pady=2).pack()

        # horizontal bar chart comparing fitness across all runs
        if len(self.all_results) > 1:
            tk.Label(self.fit_inner, text='FITNESS ACROSS ALL RUNS',
                     font=self.font_h2, fg=ACCENT, bg=BG, pady=8).pack(anchor='w')
            bar_frame = tk.Frame(self.fit_inner, bg=BG)
            bar_frame.pack(fill='x')

            all_fits = [r['best']['fitness'] for r in self.all_results]
            max_f = max(all_fits)
            min_f = min(all_fits)
            rng   = max_f - min_f if max_f != min_f else 1

            for i in range(len(self.all_results)):
                r = self.all_results[i]
                f = all_fits[i]
                row = tk.Frame(bar_frame, bg=BG)
                row.pack(fill='x', pady=1, padx=4)
                col = ACCENT3 if f == max_f else ACCENT
                tk.Label(row, text=f'Run {r["run_id"]:>2}', font=self.font_label,
                         fg=MUTED, bg=BG, width=7).pack(side='left')
                bar_w = max(4, int(((f - min_f) / rng) * 380))
                tk.Frame(row, bg=col, height=14, width=bar_w).pack(side='left')
                tk.Label(row, text=f'  {f:.4f}', font=self.font_label,
                         fg=col, bg=BG).pack(side='left')


# launches the GUI window, optionally pre-loading results
def launch_gui(best_result, all_results, students, courses, friend_pairs, config=None):
    from utils import _default_config
    if config is None:
        config = _default_config()

    root = tk.Tk()
    app  = GASchedulerGUI(root, students, courses, friend_pairs, config)

    if best_result:
        app.best_result  = best_result
        app.all_results  = all_results
        app._refresh_schedule_tab()
        app._refresh_charts_tab()
        app._refresh_fitness_tab()

    root.mainloop()


if __name__ == '__main__':
    from utils import load_courses, load_students, _default_config
    courses  = load_courses('data/course_catalog.json')
    students, friend_pairs, gc = load_students('data/student_requirements.json')
    config   = _default_config()
    launch_gui(None, [], students, courses, friend_pairs, config)
import json

class ComponentSelector:
    def __init__(self):
        self.components = self.load_components()
    
    def load_components(self):
        with open("bot/data/cpu.json", "r", encoding="utf-8") as f:
            cpu = json.load(f)
        with open("bot/data/gpu.json", "r", encoding="utf-8") as f:
            gpu = json.load(f)
        with open("bot/data/ram.json", "r", encoding="utf-8") as f:
            ram = json.load(f)
        with open("bot/data/ssd.json", "r", encoding="utf-8") as f:
            ssd = json.load(f)
        with open("bot/data/psu.json", "r", encoding="utf-8") as f:
            psu = json.load(f)
        with open("bot/data/case.json", "r", encoding="utf-8") as f:
            case = json.load(f)
        with open("bot/data/coolers.json", "r", encoding="utf-8") as f:
            coolers = json.load(f)
        with open("bot/data/motherboard.json", "r", encoding="utf-8") as f:
            motherboard = json.load(f)

        return {
            'cpu': cpu,
            'gpu': gpu,
            'ram': ram,
            'ssd': ssd,
            'psu': psu,
            'pc_case': case,
            'cooler': coolers,
            'motherboard': motherboard
        }
    
    def select_component(self, comp_list, budget, filter_func=None, sort_key=None):

        options = [c for c in comp_list if c['price'] is not None and c['price'] <= budget]
        if filter_func:
            options = [c for c in options if filter_func(c)]
        if not options:
            return None
        if sort_key:
            return max(options, key=sort_key)
        else:
            return min(options, key=lambda x: x['price'])
    
    def get_budgets_and_params(self, budget, goal):

        if goal == "games":
            return {
                'gpu': {'budget': budget * 0.5, 'sort_key': lambda x: x.get('3dmark', 0)},
                'cpu': {'budget': budget * 0.16, 'sort_key': lambda x: (x.get('cinebench_r23_single', 0), x.get('l3_cache', 0))},
                'ram': {'budget': budget * 0.07, 'sort_key': lambda x: x.get('frequency', 0)},
                'ssd': {'budget': budget * 0.04, 'sort_key': lambda x: x.get('write_speed', 0)},
                'psu': {'budget': budget * 0.07, 'sort_key': None},
                'mb': {'budget': budget * 0.1, 'sort_key': None},
                'pc_case': {'budget': budget * 0.03, 'sort_key': None},
                'cooler': {'budget': budget * 0.03, 'sort_key': None},
            }
        elif goal == "editing":
            return {
                'gpu': {'budget': budget * 0.4, 'sort_key': lambda x: x.get('vram', 0)},
                'cpu': {'budget': budget * 0.3, 'sort_key': lambda x: x.get('cinebench_r23_multi', 0)},
                'ram': {'budget': budget * 0.05, 'sort_key': lambda x: x.get('total_capacity', 0)},
                'ssd': {'budget': budget * 0.04, 'sort_key': None},
                'psu': {'budget': budget * 0.05, 'sort_key': None},
                'mb': {'budget': budget * 0.1, 'sort_key': None},
                'pc_case': {'budget': budget * 0.03, 'sort_key': None},
                'cooler': {'budget': budget * 0.03, 'sort_key': None},
            }
        elif goal == "office":
            return {
                'gpu': {'budget': 0, 'sort_key': None},
                'cpu': {'budget': budget * 0.7, 'sort_key': lambda x: x.get('cinebench_r23_multi', 0)},
                'ram': {'budget': budget * 0.05, 'sort_key': lambda x: x.get('frequency', 0)},
                'ssd': {'budget': budget * 0.04, 'sort_key': None},
                'psu': {'budget': budget * 0.05, 'sort_key': None},
                'mb': {'budget': budget * 0.1, 'sort_key': None},
                'pc_case': {'budget': budget * 0.03, 'sort_key': None},
                'cooler': {'budget': budget * 0.03, 'sort_key': None},
            }

    def select(self, budget, goal):
        components = self.load_components()
        params = self.get_budgets_and_params(budget, goal)
        build = {}

        # GPU
        gpu_budget = params['gpu']['budget']
        if gpu_budget == 0:
            build['gpu'] = None
        else:
            gpu = self.select_component(
                components['gpu'],
                gpu_budget,
                sort_key=params['gpu']['sort_key']
            )
            build['gpu'] = gpu

        # CPU
        cpu = self.select_component(
            components['cpu'],
            params['cpu']['budget'],
            sort_key=params['cpu']['sort_key']
        )
        build['cpu'] = cpu

        # MB
        if build['cpu']:
            mb_options = [m for m in components['motherboard'] if m['socket'] == build['cpu']['socket']]
            
            cpu_chipsets = build['cpu']['compatibility_mb']
            if cpu_chipsets:
                mb_options = [m for m in mb_options if m['chipset'] in cpu_chipsets]

            mb = self.select_component(
                mb_options,
                params['mb']['budget'],
                sort_key=params['mb']['sort_key']
            )
            build['motherboard'] = mb
        else:
            build['motherboard'] = None

        # RAM
        ram = self.select_component(
            components['ram'],
            params['ram']['budget'],
            sort_key=params['ram']['sort_key']
        )
        build['ram'] = ram

        # SSD
        ssd = self.select_component(
            components['ssd'],
            params['ssd']['budget'],
            sort_key=params['ssd']['sort_key']
        )
        build['ssd'] = ssd

        # PSU
        total_tdp = 0
        if build['cpu']:
            total_tdp += build['cpu']['tdp']
        if build['gpu']:
            total_tdp += build['gpu']['tdp']

        min_power = total_tdp * 1.75

        psu = self.select_component(
            components['psu'],
            params['psu']['budget'],
            filter_func=lambda p: p['power'] >= min_power,
            sort_key=params['psu']['sort_key']
        )
        build['psu'] = psu

        # Case
        if build['motherboard']:
            mb_form = build['motherboard']['form_factor']
            case_options = [c for c in components['pc_case'] if mb_form in c['form_factor']]
            case = self.select_component(
                case_options,
                params['pc_case']['budget'],
                sort_key=params['pc_case']['sort_key']
            )
            build['pc_case'] = case
        else:
            build['pc_case'] = None

        # Cooler
        cooler = self.select_component(
            components['cooler'],
            params['cooler']['budget'],
            sort_key=params['cooler']['sort_key']
        )
        build['cooler'] = cooler

        # Подсчёт общей цены
        total_price = sum([comp['price'] for comp in build.values() if comp and comp['price'] is not None])
        build['total_price'] = total_price

        return build
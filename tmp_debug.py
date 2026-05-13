import json, pathlib
p = pathlib.Path('data/bus_events.json')
q = pathlib.Path('data/bus_reservierungen.json')
events = json.loads(p.read_text(encoding='utf-8'))
reserv = json.loads(q.read_text(encoding='utf-8'))
print('events', len(events))
print('reserv', len(reserv))
print([ (e.get('id'), e.get('titel'), sum(1 for r in reserv if r.get('veranstaltung_id') == e.get('id'))) for e in events if sum(1 for r in reserv if r.get('veranstaltung_id') == e.get('id')) > 0 ])

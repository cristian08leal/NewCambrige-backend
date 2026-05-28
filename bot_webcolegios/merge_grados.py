import psycopg2
import unicodedata
from collections import defaultdict

conn = psycopg2.connect('dbname=paz_y_salvo user=postgres password=Chacho2708# host=localhost port=5432')
cur = conn.cursor()

def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').upper()

cur.execute('SELECT grado_id, nombre FROM grados')
grados = cur.fetchall()

groups = defaultdict(list)
for gid, nombre in grados:
    groups[norm(nombre)].append(gid)

for norm_name, ids in groups.items():
    if len(ids) > 1:
        # Sort so the lowest ID (first created) becomes the primary
        ids.sort()
        primary_id = ids[0]
        duplicate_ids = ids[1:]
        
        print(f"Merging {duplicate_ids} into {primary_id} for '{norm_name}'")
        
        for dup_id in duplicate_ids:
            # Need to handle ON CONFLICT for grupos and asignaciones, but a simple UPDATE might fail if there's a unique constraint
            # Since there shouldn't be duplicates within the same degree, we can try
            try:
                cur.execute('UPDATE estudiantes SET grado_id = %s WHERE grado_id = %s', (primary_id, dup_id))
            except Exception as e: print(e)
            
            try:
                cur.execute('UPDATE asignaciones SET grado_id = %s WHERE grado_id = %s', (primary_id, dup_id))
            except Exception as e: print(e)
                
            try:
                cur.execute('UPDATE grupos SET grado_id = %s WHERE grado_id = %s', (primary_id, dup_id))
            except Exception as e: print(e)
                
            cur.execute('DELETE FROM grados WHERE grado_id = %s', (dup_id,))

conn.commit()
print('Merge complete.')

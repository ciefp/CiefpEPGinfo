from enigma import eServiceReference, eTimer
from Tools.Directories import fileExists
from Tools.LoadPixmap import LoadPixmap
import os
import re
import shutil

class PiconManager:
    """Klasa za upravljanje piconima sa podrškom za podfoldere"""
    
    def __init__(self, picon_path="/media/usb/picon/"):
        self.picon_path = picon_path
        self.base_path = self.get_base_path(picon_path)
        self.cache = {}
        self.search_dirs = []
        self.picon_name_cache = {}  # Cache za imena picona
        self.build_search_dirs()
    
    def get_base_path(self, path):
        """Dohvati osnovni direktorijum"""
        if path.endswith('/picon/') or path.endswith('/picons/'):
            return path
        
        current = path.rstrip('/')
        while current and not current.endswith('/picon') and not current.endswith('/picons'):
            current = os.path.dirname(current)
            if current == '/' or current == '':
                break
        
        if current and (current.endswith('/picon') or current.endswith('/picons')):
            return current + '/'
        
        return path
    
    def build_search_dirs(self):
        """Izgradi listu direktorijuma za pretragu"""
        self.search_dirs = []
        self.picon_name_cache = {}  # Očisti cache
        
        # Uvijek dodaj /picon/ kao primarni direktorijum
        primary_paths = [
            "/picon/",
            self.picon_path,
        ]
        
        for path in primary_paths:
            if os.path.exists(path) and path not in self.search_dirs:
                self.search_dirs.append(path)
                self._index_picons_in_directory(path)
        
        # Dodaj sve podfoldere iz /picon/
        if os.path.exists("/picon/"):
            try:
                for root, dirs, files in os.walk("/picon/"):
                    # Dodaj folder ako ima PNG
                    has_png = any(f.lower().endswith('.png') for f in files)
                    if has_png and root + '/' not in self.search_dirs:
                        self.search_dirs.append(root + '/')
                        self._index_picons_in_directory(root + '/')
            except Exception as e:
                print(f"Error walking /picon/: {e}")
        
        # Dodaj sve podfoldere iz media putanja
        if os.path.exists(self.picon_path):
            try:
                for root, dirs, files in os.walk(self.picon_path):
                    has_png = any(f.lower().endswith('.png') for f in files)
                    if has_png and root + '/' not in self.search_dirs:
                        self.search_dirs.append(root + '/')
                        self._index_picons_in_directory(root + '/')
            except Exception as e:
                print(f"Error walking {self.picon_path}: {e}")
        
        # Dodaj default putanje
        default_paths = [
            "/media/usb/picon/",
            "/media/hdd/picon/",
            "/usr/share/enigma2/picon/",
        ]
        for path in default_paths:
            if os.path.exists(path) and path not in self.search_dirs:
                self.search_dirs.append(path)
                self._index_picons_in_directory(path)
        
        # Ukloni duplikate
        self.search_dirs = list(dict.fromkeys(self.search_dirs))
        print(f"Search dirs: {self.search_dirs}")
        print(f"Picon name cache has {len(self.picon_name_cache)} entries")
    
    def _index_picons_in_directory(self, directory):
        """Indeksiraj sve pikone u direktorijumu"""
        if not os.path.exists(directory):
            return
        
        try:
            for file in os.listdir(directory):
                if file.lower().endswith('.png'):
                    name_without_ext = file[:-4]
                    full_path = os.path.join(directory, file)
                    
                    # Spremi originalno ime
                    self.picon_name_cache[name_without_ext] = full_path
                    self.picon_name_cache[name_without_ext.lower()] = full_path
                    
                    # Spremi sa : umjesto _
                    name_with_colon = name_without_ext.replace('_', ':')
                    self.picon_name_cache[name_with_colon] = full_path
                    self.picon_name_cache[name_with_colon.lower()] = full_path
                    
                    # Spremi sa _ umjesto :
                    name_with_underscore = name_without_ext.replace(':', '_')
                    self.picon_name_cache[name_with_underscore] = full_path
                    self.picon_name_cache[name_with_underscore.lower()] = full_path
                    
                    # Spremi bez prefiksa p: ili c:
                    if name_without_ext.startswith('p:') or name_without_ext.startswith('c:'):
                        without_prefix = name_without_ext[2:]
                        self.picon_name_cache[without_prefix] = full_path
                        self.picon_name_cache[without_prefix.lower()] = full_path
                        
                        without_prefix_colon = without_prefix.replace('_', ':')
                        self.picon_name_cache[without_prefix_colon] = full_path
                        self.picon_name_cache[without_prefix_colon.lower()] = full_path
                        
                        without_prefix_underscore = without_prefix.replace(':', '_')
                        self.picon_name_cache[without_prefix_underscore] = full_path
                        self.picon_name_cache[without_prefix_underscore.lower()] = full_path
        except Exception as e:
            print(f"Error indexing picons in {directory}: {e}")
    
    def set_picon_path(self, path):
        """Postavi putanju do picona"""
        if os.path.exists(path):
            self.picon_path = path
            self.base_path = self.get_base_path(path)
            self.cache.clear()
            self.picon_name_cache.clear()
            self.build_search_dirs()
            return True
        return False
    
    def is_marker(self, service_ref):
        """Provjeri da li je service_ref marker (1:64)"""
        ref_clean = service_ref.replace("#SERVICE", "").strip()
        parts = ref_clean.split(":")
        if len(parts) >= 2 and parts[1] == "64":
            return True
        return False
    
    def clean_service_ref(self, service_ref):
        """Očisti service referencu i ukloni višak : na kraju"""
        ref_clean = service_ref.replace("#SERVICE", "").strip()
        # Ukloni višak : na kraju
        while ref_clean.endswith(':'):
            ref_clean = ref_clean[:-1]
        return ref_clean
    
    def find_picon(self, service_ref, channel_name=None):
        """Pronađi picon za service referencu ili ime kanala"""
        # Ignoriši markere (1:64)
        if self.is_marker(service_ref):
            return None
        
        # Očisti referencu
        ref_clean = self.clean_service_ref(service_ref)
        
        # Provjeri cache
        cache_key = ref_clean + (channel_name or "")
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Prvo pokušaj po service referenci
        possible_names = self.generate_picon_names(ref_clean)
        
        result = None
        for picon_dir in self.search_dirs:
            if not os.path.exists(picon_dir):
                continue
            
            for name in possible_names:
                picon_file = os.path.join(picon_dir, name)
                if fileExists(picon_file):
                    result = picon_file
                    break
                
                # Pokušaj sa malim slovima
                picon_file = os.path.join(picon_dir, name.lower())
                if fileExists(picon_file):
                    result = picon_file
                    break
            
            if result:
                break
        
        # Ako nije pronađen po referenci, pokušaj po imenu kanala
        if not result and channel_name:
            # Očisti ime kanala
            clean_name = channel_name
            for suffix in [" (IPTV)", " (StreamRelay)", " (HD)", " (SD)"]:
                if clean_name.endswith(suffix):
                    clean_name = clean_name[:-len(suffix)]
            
            # Pokušaj pronaći po imenu u cache-u
            clean_name_lower = clean_name.lower()
            
            # Pokušaj različite varijacije
            search_names = [
                clean_name_lower,
                clean_name_lower.replace(' ', ''),
                clean_name_lower.replace(' ', '_'),
                clean_name_lower.replace(' ', '-'),
                clean_name_lower.replace('&', 'and'),
                clean_name_lower.replace('+', 'plus'),
                clean_name_lower.replace('.', ''),
                clean_name_lower.replace("'", ''),
            ]
            
            for name in search_names:
                if name in self.picon_name_cache:
                    result = self.picon_name_cache[name]
                    break
                
                # Pokušaj sa prefixom
                for prefix in ['p:', 'c:', '']:
                    test_name = prefix + name
                    if test_name in self.picon_name_cache:
                        result = self.picon_name_cache[test_name]
                        break
                if result:
                    break
            
            # Ako i dalje nije pronađen, pokušaj STROGI partial match
            # (samo ako je ime kanala DOSTA DUGAČKO i poklapa se kao podstring)
            if not result and clean_name_lower and len(clean_name_lower) >= 4:
                for cache_name, path in self.picon_name_cache.items():
                    # Preskoči prekratka imena (tk, hd, itd.)
                    if len(cache_name) < 4:
                        continue
                    # Samo ako je CEO naziv kanala podstring picona (ne obrnuto!)
                    if clean_name_lower in cache_name:
                        result = path
                        break
        # Spremi u cache
        self.cache[cache_key] = result
        return result
    
    def generate_picon_names(self, service_ref):
        """Generiraj moguće nazive picon fajlova"""
        names = []
        
        # Očisti referencu - ukloni višak : na kraju
        ref_clean = service_ref
        while ref_clean.endswith(':'):
            ref_clean = ref_clean[:-1]
        
        # Ako je marker, vrati praznu listu
        parts = ref_clean.split(":")
        if len(parts) >= 2 and parts[1] == "64":
            return names
        
        # 1. Originalna referenca sa _ umjesto : (bez viška _ na kraju)
        names.append(ref_clean.replace(":", "_") + ".png")
        
        # 2. Generiraj različite kombinacije
        if len(parts) >= 10:
            # 1_0_19_3C3D_C90_3_EB0000_0_0_0 (svi dijelovi)
            all_parts = "_".join(parts)
            names.append(all_parts + ".png")
            
            # 1_0_19_3C3D_C90_3_EB0000 (bez zadnja tri 0)
            core = "_".join(parts[:-3])
            names.append(core + ".png")
            
            # 1_0_19_3C3D_C90_3 (bez zadnja 4)
            if len(parts) >= 7:
                core3 = "_".join(parts[:6])
                names.append(core3 + ".png")
            
            # 19_3C3D_C90_3_EB0000 (bez prvih 2)
            if len(parts) >= 7:
                core4 = "_".join(parts[2:7])
                names.append(core4 + ".png")
            
            # Samo SID:TSID:ONID
            if len(parts) >= 6:
                base = "_".join(parts[3:6])
                names.append(base + ".png")
        
        # 3. Varijante sa različitim brojem cifara u hex vrijednostima
        if len(parts) >= 6:
            try:
                sid = parts[3]
                tsid = parts[4]
                onid = parts[5]
                
                # Pokušaj sa 4-cifrenim hex
                sid_4 = f"{int(sid, 16):04x}" if sid else sid
                tsid_4 = f"{int(tsid, 16):04x}" if tsid else tsid
                onid_4 = f"{int(onid, 16):04x}" if onid else onid
                
                base_4 = "_".join([sid_4, tsid_4, onid_4])
                names.append(base_4 + ".png")
                
                # Sa satfreq
                if len(parts) >= 7:
                    satfreq = parts[6]
                    core_4 = "_".join(parts[:3] + [sid_4, tsid_4, onid_4, satfreq])
                    names.append(core_4 + ".png")
            except:
                pass
        
        # 4. Dodaj varijante sa p: i c: prefixom
        if parts[0] == "1":
            for name in names[:]:  # Kopija liste
                names.append("p:" + name)
                names.append("c:" + name)
        
        # 5. Dodaj varijante sa malim slovima
        names.extend([name.lower() for name in names])
        
        # 6. Dodaj varijante sa : umjesto _ (ako ima _)
        for name in names[:]:
            if "_" in name:
                names.append(name.replace("_", ":"))
        
        # 7. Dodaj varijante sa _ umjesto : (ako ima :)
        for name in names[:]:
            if ":" in name:
                names.append(name.replace(":", "_"))
        
        # 8. Dodaj varijante gdje je treći dio 1 umjesto 19 (različiti formati)
        if len(parts) >= 3 and parts[2].isdigit():
            # Pokušaj sa 1 umjesto 19 (neki pikoni imaju 1)
            alt_parts = parts[:]
            alt_parts[2] = "1"
            alt_name = "_".join(alt_parts) + ".png"
            names.append(alt_name)
            
            # Sa skraćenom verzijom
            if len(parts) >= 7:
                alt_core = "_".join(alt_parts[:7])
                names.append(alt_core + ".png")
        
        # 9. Ukloni duplikate i prazne, i ukloni višak _ na kraju prije .png
        unique_names = []
        for name in names:
            if name and name.endswith('.png'):
                # Ukloni višak _ prije .png
                base = name[:-4]
                while base.endswith('_'):
                    base = base[:-1]
                clean_name = base + '.png'
                if clean_name not in unique_names:
                    unique_names.append(clean_name)
            elif name:
                if name not in unique_names:
                    unique_names.append(name)
        
        return unique_names
    
    def get_picon_pixmap(self, service_ref, channel_name=None):
        """Dohvati picon kao pixmap"""
        # Ignoriši markere
        if self.is_marker(service_ref):
            return None
        
        picon_file = self.find_picon(service_ref, channel_name)
        if picon_file:
            return LoadPixmap(picon_file)
        return None

    def assign_picon(self, service_ref, source_file):
        """Dodijeli picon kanalu - kopira u /picon/ i ostavlja original"""
        if self.is_marker(service_ref):
            return False
        
        try:
            # Očisti referencu - ukloni višak :
            ref_clean = self.clean_service_ref(service_ref)
            picon_name = ref_clean.replace(":", "_") + ".png"
            
            # 1. Prvo kopiraj u /picon/ (primarna lokacija)
            primary_target = os.path.join("/picon/", picon_name)
            
            # Provjeri da li /picon/ postoji, ako ne, kreiraj
            if not os.path.exists("/picon/"):
                try:
                    os.makedirs("/picon/")
                except:
                    pass
            
            # Kopiraj u /picon/
            try:
                shutil.copy2(source_file, primary_target)
                print(f"[PiconManager] Copied to /picon/: {primary_target}")
            except Exception as e:
                print(f"[PiconManager] Error copying to /picon/: {e}")
            
            # 2. Takođe kopiraj u trenutni folder (media)
            media_target = os.path.join(self.picon_path, picon_name)
            try:
                shutil.copy2(source_file, media_target)
                print(f"[PiconManager] Copied to media: {media_target}")
            except Exception as e:
                print(f"[PiconManager] Error copying to media: {e}")
            
            # 3. Ažuriraj cache
            self.cache[ref_clean] = primary_target
            self.build_search_dirs()
            
            return True
        except Exception as e:
            print(f"Error assigning picon: {e}")
            return False

    def delete_picon(self, service_ref):
        """Obriši picon za kanal - briše iz svih lokacija"""
        if self.is_marker(service_ref):
            return False
        
        # Očisti referencu
        ref_clean = self.clean_service_ref(service_ref)
        picon_name = ref_clean.replace(":", "_") + ".png"
        
        deleted = False
        
        # 1. Obriši iz /picon/
        primary_file = os.path.join("/picon/", picon_name)
        if fileExists(primary_file):
            try:
                os.remove(primary_file)
                deleted = True
                print(f"[PiconManager] Deleted from /picon/: {primary_file}")
            except Exception as e:
                print(f"[PiconManager] Error deleting from /picon/: {e}")
        
        # 2. Obriši iz media foldera
        media_file = os.path.join(self.picon_path, picon_name)
        if fileExists(media_file):
            try:
                os.remove(media_file)
                deleted = True
                print(f"[PiconManager] Deleted from media: {media_file}")
            except Exception as e:
                print(f"[PiconManager] Error deleting from media: {e}")
        
        # 3. Obriši iz svih podfoldera
        for picon_dir in self.search_dirs:
            if picon_dir not in ["/picon/", self.picon_path]:
                picon_file = os.path.join(picon_dir, picon_name)
                if fileExists(picon_file):
                    try:
                        os.remove(picon_file)
                        deleted = True
                        print(f"[PiconManager] Deleted from {picon_dir}")
                    except Exception as e:
                        print(f"[PiconManager] Error deleting from {picon_dir}: {e}")
        
        # 4. Ažuriraj cache
        self.cache[ref_clean] = None
        self.build_search_dirs()
        
        return deleted
    
    def get_picons_from_selected_folder(self):
        """Dohvati samo pikone iz selektiranog foldera"""
        picon_files = []
        
        if not os.path.exists(self.picon_path):
            return picon_files
        
        try:
            for file in os.listdir(self.picon_path):
                if file.lower().endswith('.png'):
                    full_path = os.path.join(self.picon_path, file)
                    if os.path.isfile(full_path):
                        display_name = file.replace('.png', '').replace('_', ':')
                        if len(display_name) > 40:
                            display_name = display_name[:37] + "..."
                        picon_files.append((display_name, full_path, file))
            
            picon_files.sort(key=lambda x: x[0])
        except Exception as e:
            print(f"Error getting picons from selected folder: {e}")
        
        return picon_files
    
    def get_all_picons(self):
        """Dohvati sve pikone iz svih direktorijuma"""
        picon_files = []
        
        for picon_dir in self.search_dirs:
            if not os.path.exists(picon_dir):
                continue
            
            try:
                for file in os.listdir(picon_dir):
                    if file.lower().endswith('.png'):
                        full_path = os.path.join(picon_dir, file)
                        if os.path.isfile(full_path):
                            display_name = file.replace('.png', '').replace('_', ':')
                            if len(display_name) > 40:
                                display_name = display_name[:37] + "..."
                            dir_name = os.path.basename(picon_dir.rstrip('/'))
                            if dir_name and dir_name not in ["picon", "picons", "media", "usb", "hdd"]:
                                display_name = f"[{dir_name}] {display_name}"
                            picon_files.append((display_name, full_path, file))
            except Exception as e:
                print(f"Error getting picons from {picon_dir}: {e}")
        
        seen = set()
        unique_picons = []
        for p in picon_files:
            if p[2] not in seen:
                seen.add(p[2])
                unique_picons.append(p)
        
        unique_picons.sort(key=lambda x: x[0])
        return unique_picons
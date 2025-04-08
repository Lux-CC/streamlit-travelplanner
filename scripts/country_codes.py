import requests
import pycountry
import time
from lib.cache import cache_response

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def get_area_id_for_country(iso_code: str, country_name: str) -> int | None:
    query = f"""
    [out:json][timeout:25];
    relation["admin_level"="2"]["boundary"="administrative"]
      ["ISO3166-1"="{iso_code}"];
    out ids;
    """
    response = requests.post(OVERPASS_URL, data={"data": query})
    response.raise_for_status()
    data = response.json()

    if data["elements"]:
        return 3600000000 + data["elements"][0]["id"]

    # Fallback: try matching by exact name
    name_query = f"""
    [out:json][timeout:25];
    relation["admin_level"="2"]["boundary"="administrative"]
      ["name"="{country_name}"];
    out ids;
    """
    response = requests.post(OVERPASS_URL, data={"data": name_query})
    response.raise_for_status()
    data = response.json()

    if data["elements"]:
        return 3600000000 + data["elements"][0]["id"]

    return None


def generate_all_country_area_ids(sleep_seconds=1.2):
    result = {}
    countries = list(pycountry.countries)

    for country in countries:
        iso = country.alpha_2
        name = country.name
        print(f"🔍 {iso}: {name}")
        try:
            area_id = get_area_id_for_country(iso, name)
            if area_id:
                print(f"✅ {iso} → {area_id}")
                result[iso] = area_id
            else:
                print(f"⚠️  Not found: {iso}")
        except Exception as e:
            print(f"❌ Error for {iso}: {e}")
        time.sleep(sleep_seconds)  # prevent rate limit

    return result


def save_as_python_module(mapping: dict, filename="country_area_ids.py"):
    with open(filename, "w") as f:
        f.write("# country_area_ids.py\n\n")
        f.write("COUNTRY_AREA_IDS = {\n")
        for iso, area_id in sorted(mapping.items()):
            f.write(f'    "{iso}": {area_id},\n')
        f.write("}\n")


if __name__ == "__main__":
    print("🚀 Generating country → area ID mapping...")
    mapping = generate_all_country_area_ids()
    save_as_python_module(mapping)
    print(f"\n✅ Done! {len(mapping)} countries saved to country_area_ids.py")

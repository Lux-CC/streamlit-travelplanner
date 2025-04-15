import folium
from folium.plugins import MarkerCluster
from lib.cache import time_function
from lib.geo_resolver import resolve_geo_query
import streamlit as st


@time_function
def render_brainstorm_locations(
    brainstorm_data,
    selected_statuses,
    selected_countries,
):
    """
    Returns a folium map and debug logs with brainstorm locations rendered.
    """
    print("==========")
    print("start debug locations")
    print(
        f"location: {st.session_state.get("center", {}).get("lat", 10)}, {st.session_state.get("center", {}).get("lng", 10)}",
    )
    print(f"zoom: {st.session_state.get("zoom", 4)}")
    print(f"end debug locations")
    map_view = folium.Map(
        location=[
            10,
            100,
        ],
        zoom_start=4,
        tiles="cartodb positron",
        prefer_canvas=True,
        disable_3d=True,
    )
    resolved = []
    debug_logs = []

    country_group = folium.FeatureGroup(name="Country Outlines", show=True)
    region_group = folium.FeatureGroup(name="Regions", show=True)
    place_group = folium.FeatureGroup(name="Places", show=True)
    icon_create_function = """
    function(cluster) {
        return L.divIcon({
            html: '<div style="background-color: green; border-radius: 50%; width: 30px; height: 30px; display: flex; justify-content: center; align-items: center;"><span style="color: white;">' + cluster.getChildCount() + '</span></div>',
            className: 'custom-cluster',
            iconSize: new L.Point(30, 30)
        });
    }
"""

    marker_cluster = MarkerCluster(
        name="Clustered Places", icon_create_function=icon_create_function
    )

    # Draw country outlines based on selected filters
    unique_countries = {
        item["country"]
        for item in brainstorm_data
        if item.get("metadata", {}).get("status") in selected_statuses
        and item.get("country") in selected_countries
    }
    for country in sorted(unique_countries):
        result, _ = resolve_geo_query(country)
        if result and "geojson" in result:
            folium.GeoJson(
                result["geojson"],
                name=f"{country}-outline",
                smooth_factor=10,
                style_function=lambda feature: {
                    "fillColor": "#00000000",
                    "color": "#444444",
                    "weight": 1.5,
                    "dashArray": "5,5",
                    "fillOpacity": 0.0,
                },
            ).add_to(country_group)

    # Draw each brainstorm item
    for item in brainstorm_data:
        if item.get("metadata", {}).get("status") not in selected_statuses:
            continue
        if item.get("country") not in selected_countries:
            continue

        result, cache_hit = resolve_geo_query(item["geo_query"])
        if not result:
            st.toast(f"❌ No results found for query: {item["geo_query"]}")

        debug_logs.append(f"{'✅' if cache_hit else '🆕'} {item['geo_query']}")

        if result and "error" not in result:
            result["id"] = item["id"]
            result["popup_id"] = item["id"]
            result["tooltip_text"] = f"{item['name']}<br>" + "<br>".join(
                [a["text"] for a in item.get("annotations", [])]
            )
            resolved.append(result)

            image_urls = item.get("metadata", {}).get("images", [])[:2]
            image_html = "".join(
                f'<img src="{url}" style="max-width:100px; height:auto; margin-right:5px;">'
                for url in image_urls
            )

            popup_html = f"""
            <b>{item['name']}</b><br><br>
            {image_html}<br><br>
            {"<br>".join(a['text'] for a in item.get('annotations', []))}
            """
            score = item.get("metadata", {}).get("score", 0)
            if score >= 0.9:
                marker_color = "green"
                fill_color = "#1a9850"  # dark green
            elif score >= 0.8:
                marker_color = "lightgreen"
                fill_color = "#66bd63"  # medium green
            elif score >= 0.6:
                marker_color = "beige"
                fill_color = "#fee08b"  # warm yellow
            else:
                marker_color = "lightred"
                fill_color = "#d73027"  # strong red

            if result.get("geojson"):
                folium.GeoJson(
                    data=result["geojson"],
                    tooltip=item["id"],
                    # popup=folium.Popup(
                    #     popup_html,
                    #     max_width=250,
                    # ),
                    zoom_on_click=True,
                    marker=folium.CircleMarker(radius=4, fill=True, color="red"),
                    name=item["name"],
                    smooth_factor=5,
                    style_function=lambda feature, fill=fill_color: {
                        "fillColor": fill,
                        "color": "black",
                        "weight": 1,
                        "fillOpacity": 0.3,
                    },
                ).add_to(region_group)

            folium.Marker(
                [result["lat"], result["lon"]],
                popup=folium.Popup(
                    popup_html,
                    max_width=250,
                ),
                tooltip=item["id"],
                icon=folium.Icon(
                    color=marker_color,
                    icon="info-sign" if result.get("geojson") else "pushpin",
                ),
            ).add_to(marker_cluster)

    country_group.add_to(map_view)
    region_group.add_to(map_view)
    marker_cluster.add_to(place_group)
    place_group.add_to(map_view)
    st.session_state.feature_group_to_add = place_group  # debug for dynamic maps
    folium.LayerControl(collapsed=False).add_to(map_view)
    st.session_state.debug_logs = st.session_state.get("debug_logs", []) + debug_logs
    return map_view

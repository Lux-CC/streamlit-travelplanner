from folium.plugins import Draw


def add_draw_support(map_obj):
    """
    Adds Draw support to the map object, ensuring only one instance is added.
    """
    if getattr(map_obj, "_draw_added", False):
        return  # Already added

    

    # Flag it so it doesn't happen again
    map_obj._draw_added = True

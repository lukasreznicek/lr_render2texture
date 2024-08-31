import flet as ft

def main(page):
    page.title = "Draggable List Tiles"

    # Create a list of initial items (customize as needed)
    initial_items = ["Item 1", "Item 2", "Item 3", "Item 4"]

    # Initialize an empty list to store draggable controls
    draggable_list = []

    # Create draggable list tiles
    for item_text in initial_items:
        draggable = ft.Draggable(
            group="my_drag_group",  # Specify a unique group for drag-and-drop
            content=ft.ListTile(title=ft.Text(item_text)),
        )
        draggable_list.append(draggable)

    # Create a container to hold the draggable list tiles
    draggable_container = ft.Container(
        width=500,
        content=ft.Column(draggable_list),
    )

    page.add(draggable_container)

ft.app(target=main)

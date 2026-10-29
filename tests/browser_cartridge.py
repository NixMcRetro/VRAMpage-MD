"""Exercise cartridge choices through the same direct actions as browser users."""


def choose_cartridge(page, cartridge_id):
    page.locator('#cartridgeChooser > summary').click()
    page.locator(f'#cartridgeChooser button[data-cartridge="{cartridge_id}"]').click()

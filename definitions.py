"""
Definitions of the different overlays. See overlay.forms::create_data_form for more detailed information
"""

lower_third_definition = [
    ('title', '', str, 'string'),
    ('subtitle', '', str, 'string'),
    ('fadein', 1000, int, 'integer'),
    ('hold', 6000, int, 'integer'),
    ('fadeout', 1000, int, 'integer'),
    ('title_color', '#242582', str, 'color'),
    ('subtitle_color', '#2F2FA2', str, 'color'),
    ('title_text_color', '#FFFFFF', str, 'color'),
    ('subtitle_text_color', '#FFFFFF', str, 'color')
]

social_media_definition = [
    ('message', '', str, 'string'),
    ('tag', '', str, 'string'),
    ('fadein', 1000, int, 'integer'),
    ('hold', 6000, int, 'integer'),
    ('fadeout', 1000, int, 'integer'),
    ('message_color', '#242582', str, 'color'),
    ('tag_color', '#2F2FA2', str, 'color'),
    ('message_text_color', '#FFFFFF', str, 'color'),
    ('tag_text_color', '#FFFFFF', str, 'color')
]

centered_title_definition = [
    ('title', '', str, 'string'),
    ('fadein', 1000, int, 'integer'),
    ('hold', 6000, int, 'integer'),
    ('fadeout', 1000, int, 'integer'),
    ('title_size', '42px', str, 'string'),
    ('title_color', '#242582', str, 'color'),
    ('title_text_color', '#FFFFFF', str, 'color')
]

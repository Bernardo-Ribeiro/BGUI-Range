window.UI_BUILDER_CONSTANTS = {
  DEFAULT_FONT_BASE: '../range 1.6/bgui/fonts',
  DEFAULT_THEME_CANDIDATES: [
    '../range 1.6/bgui/themes/default/theme.cfg',
    './range 1.6/bgui/themes/default/theme.cfg',
    '/range%201.6/bgui/themes/default/theme.cfg'
  ],
  PY_WIDGET_DEFAULTS: {
    Label: { text: '', pos: '0,0' },
    Slider: { value: '0.0', min_value: '0.0', max_value: '1.0', size: '100,20', pos: '0,0', sub_theme: '' },
    Button: { text: '', size: '1,1', pos: '0,0', sub_theme: '' },
    ProgressBar: { percent: '1.0', size: '1,1', pos: '0,0', sub_theme: '' },
    Frame: { size: '1,1', pos: '0,0', sub_theme: '' },
    Image: { img: '', size: '1,1', pos: '0,0', sub_theme: '' },
    ImageButton: { default_image: '', default2_image: '', hover_image: '', click_image: '', size: '1,1', pos: '0,0', sub_theme: '' },
    ListBox: { items: '', padding: '0', size: '1,1', pos: '0,0', sub_theme: '' },
    TextBlock: { text: '', size: '1,1', pos: '0,0', sub_theme: '' },
    TextInput: { text: '', prefix: '', size: '1,1', pos: '0,0', sub_theme: '' },
    Video: { vid: '', play_audio: '0', repeat: '0', size: '1,1', pos: '0,0', sub_theme: '' }
  },
  REQUIRED_ATTRS: {
    Image: ['img'],
    Video: ['vid']
  }
};

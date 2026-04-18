// addon_display_light.cpp - Display light component state definitions

#ifdef NSPANEL_EASY_ADDON_DISPLAY_LIGHT

#include "addon_display_light.h"

namespace esphome::nspanel_easy {

bool display_light_updating = false;  // Flag to prevent feedback loop when light component triggers set_brightness

}  // namespace esphome::nspanel_easy

#endif  // NSPANEL_EASY_ADDON_DISPLAY_LIGHT

// addon_display_light.h - Handle the display brighness/sleep as a light

#pragma once

#ifdef NSPANEL_EASY_ADDON_DISPLAY_LIGHT

namespace esphome::nspanel_easy {

extern bool display_light_updating;  // Flag to prevent feedback loop when light component triggers set_brightness

}  // namespace esphome::nspanel_easy

#endif  // NSPANEL_EASY_ADDON_DISPLAY_LIGHT

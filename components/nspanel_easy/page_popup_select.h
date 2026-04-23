// page_popup_select.h

#pragma once

#ifdef NSPANEL_EASY_PAGE_POPUP_SELECT

#include <string>
#include <vector>

namespace esphome::nspanel_easy {

extern std::string popup_select_cache_entity;
extern std::string popup_select_cache_context;
extern uint8_t popup_select_cache_mode;
extern uint32_t popup_select_cache_mask;
extern std::vector<std::string> popup_select_cache_options;

}  // namespace esphome::nspanel_easy

#endif  // NSPANEL_EASY_PAGE_POPUP_SELECT

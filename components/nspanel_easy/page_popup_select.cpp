// page_popup_select.cpp

#ifdef NSPANEL_EASY_PAGE_POPUP_SELECT

#include "page_popup_select.h"

namespace esphome::nspanel_easy {

std::string popup_select_cache_entity;
std::string popup_select_cache_context;
uint8_t popup_select_cache_mode = UINT8_MAX;
uint32_t popup_select_cache_mask = 0;
std::vector<std::string> popup_select_cache_options;

}  // namespace esphome::nspanel_easy

#endif  // NSPANEL_EASY_PAGE_POPUP_SELECT

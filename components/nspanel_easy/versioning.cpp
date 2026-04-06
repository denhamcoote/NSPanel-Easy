// versioning.cpp

#ifdef NSPANEL_EASY_VERSIONING

#include "versioning.h"

namespace esphome::nspanel_easy {

bool calver_gte(const std::string &version, const std::string &min_version) {
  int ver_y = 0, ver_m = 0, ver_s = 0;
  int min_y = 0, min_m = 0, min_s = 0;

  // Parse both version strings — fail safe if either is malformed or empty.
  // An empty string produces 0 fields parsed, triggering the != 3 guard below.
  // sscanf with exact field count check (!=3) is safe here; NOLINT
  // suppresses cert-err34-c which flags sscanf for non-numeric input,
  // but malformed input is handled by the field count check below.
  if (sscanf(version.c_str(), "%d.%d.%d", &ver_y, &ver_m, &ver_s) != 3 ||      // NOLINT(cert-err34-c)
      sscanf(min_version.c_str(), "%d.%d.%d", &min_y, &min_m, &min_s) != 3) {  // NOLINT(cert-err34-c)
    return false;
  }

  // Compare year first, then month, then sequence number.
  // Returns false conservatively on any older segment.
  if (ver_y != min_y)
    return ver_y > min_y;
  if (ver_m != min_m)
    return ver_m > min_m;
  return ver_s >= min_s;
}

bool tft_ver_gte(const std::string &version, const std::string &min_version) {
  int ver_maj = 0, ver_min = 0;
  int min_maj = 0, min_min = 0;

  // Parse both version strings — accept "major.minor" or bare "major".
  // sscanf returns the number of fields successfully parsed; at least 1
  // is required. A bare integer (e.g. "16") yields 1 field with minor
  // defaulting to 0. An empty or non-numeric string yields 0, triggering
  // the < 1 guard below. NOLINT suppresses cert-err34-c; malformed input
  // is handled by the field count check.
  const int ver_fields = sscanf(version.c_str(), "%d.%d", &ver_maj, &ver_min);      // NOLINT(cert-err34-c)
  const int min_fields = sscanf(min_version.c_str(), "%d.%d", &min_maj, &min_min);  // NOLINT(cert-err34-c)

  if (ver_fields < 1 || min_fields < 1)
    return false;  // Fail conservatively on empty or unparseable input

  // Compare major first, then minor.
  // Returns false conservatively on any older segment.
  if (ver_maj != min_maj)
    return ver_maj > min_maj;
  return ver_min >= min_min;
}

}  // namespace esphome::nspanel_easy

#endif  // NSPANEL_EASY_VERSIONING

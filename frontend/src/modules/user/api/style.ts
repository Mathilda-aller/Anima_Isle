import { request } from "@/infrastructure/http/request";
import type { UserDTO } from "@/modules/auth/types/auth";

interface UserStyleUpdate {
  style_pref: "Warm" | "Dark";
}

export function updateUserStyle(stylePref: "Warm" | "Dark") {
  return request<UserDTO, UserStyleUpdate>({
    path: "/users/style",
    method: "POST",
    data: { style_pref: stylePref },
  });
}

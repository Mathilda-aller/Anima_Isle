export async function getWechatCode(): Promise<string> {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    uni.login({
      provider: "weixin",
      success: (res) => {
        if (res.code) {
          resolve(res.code);
          return;
        }
        reject(new Error("empty_wechat_code"));
      },
      fail: (err) => reject(err),
    });
    // #endif

    // #ifndef MP-WEIXIN
    reject(new Error("wechat_login_only_supported_in_mp_weixin"));
    // #endif
  });
}

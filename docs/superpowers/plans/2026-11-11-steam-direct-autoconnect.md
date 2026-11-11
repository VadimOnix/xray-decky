# Steam Direct and Autoconnect

**Goal:** Start the selected profile after the Deck gets a physical default route. Keep Steam services on the physical interface while TUN carries other Internet traffic.

- [x] Test separate Steam destination rules in both proxy cores, including Valve IP ranges and an unchanged default proxy route.
- [x] Expose opt-in settings in the Decky and desktop panels and test startup, manual disconnect, and route repair.
- [x] Update dependencies and verify the pinned cores, build, and test suite.
- [x] Install the fork and compare direct and proxy traffic after reboot.
- [x] Repeat the routing check after the Deck wakes from suspend.

Steam domains and Valve's AS32590 prefixes define the exception. Shared CDN domains and third-party game servers continue to use the default route unless their destination matches a Steam rule.

On SteamOS 3.9.5, build 2.3.3-steam.3 connected automatically after reboot. After reboot and resume, the Steam store request increased the direct outbound counter, and the Cloudflare request increased the proxy counter and reported a different public IP from the direct connection. The Deck's network had an IPv4 default route.

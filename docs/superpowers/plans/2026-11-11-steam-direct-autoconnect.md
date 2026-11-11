# Steam Direct and Autoconnect

**Goal:** Start the selected profile after the Deck gets a physical default route. Keep Steam services on the physical interface while TUN carries other Internet traffic.

- [x] Test separate Steam destination rules in both proxy cores, including Valve IP ranges and an unchanged default proxy route.
- [x] Expose opt-in settings in the Decky and desktop panels and test startup, manual disconnect, and route repair.
- [x] Update dependencies and verify the pinned cores, build, and test suite.
- [x] Install the fork and compare direct and proxy traffic after reboot.
- [ ] Repeat the routing check after the Deck wakes from suspend.

Steam domains and Valve's AS32590 prefixes define the exception. Shared CDN domains and third-party game servers continue to use the default route unless their destination matches a Steam rule.

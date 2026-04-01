import AppKit
import SwiftUI
import os.log

class AppDelegate: NSObject, NSApplicationDelegate {
    private let logger = Logger(subsystem: "com.vibereader.menubar", category: "AppDelegate")
    var statusItem: NSStatusItem!
    var popover: NSPopover!
    var appState = AppState()
    var refreshTimer: Timer?
    var statusTimer: Timer?

    func applicationDidFinishLaunching(_ notification: Notification) {
        logger.info("launching...")

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem.button {
            button.title = "V"
            button.action = #selector(togglePopover(_:))
            button.target = self
        }

        popover = NSPopover()
        popover.contentSize = NSSize(width: 380, height: 500)
        popover.behavior = .transient
        popover.contentViewController = NSHostingController(
            rootView: PopoverContentView(state: appState)
        )

        Task { await appState.fetchArticles() }
        Task { await appState.fetchStatus() }

        // Block-based timers to avoid retain cycles
        let rTimer = Timer(timeInterval: 60, repeats: true) { [weak self] _ in
            guard let self else { return }
            Task { await self.appState.fetchArticles() }
        }
        RunLoop.main.add(rTimer, forMode: .common)
        refreshTimer = rTimer

        let sTimer = Timer(timeInterval: 10, repeats: true) { [weak self] _ in
            guard let self else { return }
            Task { await self.appState.fetchStatus() }
            self.updateIcon()
        }
        RunLoop.main.add(sTimer, forMode: .common)
        statusTimer = sTimer

        logger.info("ready")
    }

    @objc func togglePopover(_ sender: Any?) {
        guard let button = statusItem.button else { return }
        if popover.isShown {
            popover.performClose(sender)
        } else {
            popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            popover.contentViewController?.view.window?.makeKey()
        }
    }

    func updateIcon() {
        guard let button = statusItem.button else { return }
        button.contentTintColor = appState.claudeActive ? .systemGreen : nil
    }
}

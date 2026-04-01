import Foundation
import os.log

final class NotificationManager {
    private let logger = Logger(subsystem: "com.vibereader.menubar", category: "NotificationManager")
    private(set) var lastNotificationTime: Date = .distantPast
    private(set) var notifiedArticleIds: Set<String> = []

    func notify(articles: [Article]) {
        // Cooldown: skip if less than 5 minutes since last notification
        guard Date().timeIntervalSince(lastNotificationTime) > 300 else {
            return
        }

        // Always update cooldown timestamp to prevent repeated calls
        lastNotificationTime = Date()

        // Filter out already-notified articles
        let unnotified = articles.filter { !notifiedArticleIds.contains($0.id) }
        let picks = Array(unnotified.prefix(3))
        guard !picks.isEmpty else { return }

        for article in picks {
            notifiedArticleIds.insert(article.id)
        }

        // Build notification body
        let body = picks.enumerated().map { i, a in
            let t = a.title.count > 55 ? String(a.title.prefix(52)) + "..." : a.title
            return "\(i + 1). \(t)"
        }.joined(separator: "\n")

        // Use osascript for notifications (SPM binary target lacks a bundle ID)
        let escaped = body.replacingOccurrences(of: "\"", with: "\\\"")
            .replacingOccurrences(of: "\\", with: "\\\\")
        let script = "display notification \"\(escaped)\" with title \"While Claude works...\""

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        process.arguments = ["-e", script]
        do {
            try process.run()
            logger.info("Notification sent: \(picks.count) articles")
        } catch {
            logger.error("Notification failed: \(error.localizedDescription)")
        }
    }
}

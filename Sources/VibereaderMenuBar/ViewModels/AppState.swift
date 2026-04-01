import Foundation
import SwiftUI
import os.log

@MainActor
final class AppState: ObservableObject {
    private let logger = Logger(subsystem: "com.vibereader.menubar", category: "AppState")

    // Services
    let articleService = ArticleService()
    let statusService = StatusService()
    let notificationManager = NotificationManager()

    // Published state
    @Published var articles: [Article] = []
    @Published var lastFetched: Date? = nil
    @Published var isRefreshing: Bool = false
    @Published var searchText: String = ""
    @Published var claudeActive: Bool = false

    // Private coordination state (not published — no UI bindings)
    private var wasClaudeActive: Bool = false

    // Computed: filtered articles for the view
    var filteredArticles: [Article] {
        let sorted = articles.sorted { $0.score > $1.score }
        let top = Array(sorted.prefix(15))
        if searchText.isEmpty { return top }
        return top.filter { a in
            a.title.localizedCaseInsensitiveContains(searchText) ||
            a.source.localizedCaseInsensitiveContains(searchText) ||
            a.categories.contains { $0.localizedCaseInsensitiveContains(searchText) }
        }
    }

    // MARK: - Actions

    func fetchArticles() async {
        do {
            let feed = try await articleService.fetchArticles()
            let serverDate = ISO8601DateFormatter().date(from: feed.fetchedAt) ?? Date()
            withAnimation {
                articles = feed.articles
                lastFetched = serverDate
            }
        } catch {
            logger.error("fetchArticles: \(error.localizedDescription)")
        }
    }

    func fetchStatus() async {
        do {
            let status = try await statusService.fetchStatus()
            let justBecameActive = status.claudeActive && !wasClaudeActive
            claudeActive = status.claudeActive
            wasClaudeActive = status.claudeActive

            if justBecameActive {
                notificationManager.notify(articles: filteredArticles)
            }
        } catch {
            logger.error("fetchStatus: \(error.localizedDescription)")
        }
    }

    func refreshFeed() async {
        isRefreshing = true
        defer { isRefreshing = false }

        do {
            try await articleService.refreshFeed()
            let feed = try await articleService.pollForUpdate(oldFetchedAt: lastFetched)
            let serverDate = ISO8601DateFormatter().date(from: feed.fetchedAt) ?? Date()
            withAnimation {
                articles = feed.articles
                lastFetched = serverDate
            }
        } catch {
            logger.error("refreshFeed: \(error.localizedDescription)")
        }
    }
}

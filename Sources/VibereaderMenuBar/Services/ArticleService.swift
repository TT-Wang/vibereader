import Foundation
import os.log

final class ArticleService {
    private let logger = Logger(subsystem: "com.vibereader.menubar", category: "ArticleService")

    func fetchArticles() async throws -> FeedResponse {
        guard let url = URL(string: "\(Config.apiURL)/api/articles") else {
            throw URLError(.badURL)
        }
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(FeedResponse.self, from: data)
    }

    func refreshFeed() async throws {
        guard let url = URL(string: "\(Config.apiURL)/refresh") else {
            throw URLError(.badURL)
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let (_, response) = try await URLSession.shared.data(for: request)
        if let http = response as? HTTPURLResponse {
            logger.info("refreshFeed: \(http.statusCode)")
        }
    }

    func pollForUpdate(oldFetchedAt: Date?) async throws -> FeedResponse {
        for attempt in 0..<8 {
            try await Task.sleep(for: .seconds(2))
            let feed = try await fetchArticles()
            let serverDate = ISO8601DateFormatter().date(from: feed.fetchedAt)
            if serverDate != nil && serverDate != oldFetchedAt {
                logger.info("pollForUpdate: articles updated on attempt \(attempt + 1)")
                return feed
            }
        }
        logger.warning("pollForUpdate: timed out after 8 attempts")
        throw URLError(.timedOut)
    }
}

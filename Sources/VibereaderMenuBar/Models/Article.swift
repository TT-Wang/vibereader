import Foundation

struct Article: Decodable {
    let id: String
    let title: String
    let url: String
    let source: String
    let score: Double
    let categories: [String]
}

struct FeedResponse: Decodable {
    let articles: [Article]
    let fetchedAt: String

    enum CodingKeys: String, CodingKey {
        case articles
        case fetchedAt = "fetched_at"
    }
}

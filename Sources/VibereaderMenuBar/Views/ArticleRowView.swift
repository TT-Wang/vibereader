import SwiftUI
import AppKit

struct ArticleRowView: View {
    let article: Article
    @State private var isHovered = false

    var body: some View {
        Button {
            if let url = URL(string: article.url) {
                NSWorkspace.shared.open(url)
            }
        } label: {
            VStack(alignment: .leading, spacing: 6) {
                Text(article.title)
                    .font(.system(size: 13, weight: .semibold))
                    .lineLimit(2)
                    .foregroundColor(.primary)

                HStack(spacing: 6) {
                    Text(String(format: "%.1f", article.score))
                        .font(.system(size: 10, weight: .bold))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(scoreColor.opacity(0.2))
                        .foregroundColor(scoreColor)
                        .clipShape(RoundedRectangle(cornerRadius: 4))

                    ForEach(article.categories.prefix(3), id: \.self) { cat in
                        Text(cat)
                            .font(.system(size: 9))
                            .padding(.horizontal, 5)
                            .padding(.vertical, 2)
                            .background(Color.purple.opacity(0.15))
                            .foregroundColor(.purple)
                            .clipShape(RoundedRectangle(cornerRadius: 4))
                    }

                    Spacer()

                    Text(article.source)
                        .font(.system(size: 10))
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(isHovered ? Color.primary.opacity(0.06) : Color.clear)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovered = hovering
            }
        }
    }

    var scoreColor: Color {
        if article.score > 2.0 { return .green }
        if article.score > 1.0 { return .yellow }
        return .gray
    }
}

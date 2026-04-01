import SwiftUI
import AppKit

struct PopoverContentView: View {
    @ObservedObject var state: AppState

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Vibereader")
                    .font(.headline)
                    .fontWeight(.bold)
                Circle()
                    .fill(state.claudeActive ? Color.green : Color.gray)
                    .frame(width: 8, height: 8)
                    .help(state.claudeActive ? "Claude is working" : "Claude is idle")
                Spacer()
                Text(timeAgoText)
                    .font(.caption)
                    .foregroundColor(.secondary)
                Button {
                    Task { await state.refreshFeed() }
                } label: {
                    if state.isRefreshing {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 12))
                    }
                }
                .buttonStyle(.borderless)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)

            Divider()

            // Search bar
            TextField("Search articles...", text: $state.searchText)
                .textFieldStyle(.roundedBorder)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)

            Divider()

            // Article list
            ScrollView {
                LazyVStack(spacing: 0) {
                    ForEach(state.filteredArticles, id: \.id) { article in
                        ArticleRowView(article: article)
                        Divider()
                    }
                }
            }

            Divider()

            // Footer
            Button("Quit Vibereader") {
                NSApplication.shared.terminate(nil)
            }
            .buttonStyle(.borderless)
            .font(.caption)
            .foregroundColor(.secondary)
            .padding(.vertical, 8)
        }
        .frame(width: 380, height: 500)
        .background(Color(nsColor: .windowBackgroundColor))
    }

    var timeAgoText: String {
        guard let date = state.lastFetched else { return "never" }
        let minutes = Int(Date().timeIntervalSince(date) / 60)
        if minutes < 1 { return "just now" }
        if minutes < 60 { return "\(minutes)m ago" }
        return "\(minutes / 60)h ago"
    }
}

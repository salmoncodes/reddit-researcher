"""Rule-based tagging for posts."""

import re


# Define tags with associated keywords
TAG_RULES = {
    "note_taking": [
        "note taking",
        "notes",
        "notetaking",
        "note-taking",
        "onenote",
        "notion",
        "obsidian",
        "evernote",
        "notebook",
    ],
    "flashcards": ["flashcard", "anki", "quizlet", "spaced repetition", "srs"],
    "quizzes": ["quiz", "practice test", "mock exam", "practice questions"],
    "summarization": ["summary", "summarize", "tldr", "summarise", "condense"],
    "lecture_slides": [
        "slides",
        "powerpoint",
        "presentation",
        "lecture notes",
        "slideshow",
        "pptx",
    ],
    "podcasts": ["podcast", "audio", "listen", "spotify", "audible"],
    "productivity_tools": [
        "productivity",
        "pomodoro",
        "focus",
        "timer",
        "forest",
        "todoist",
        "task manager",
    ],
    "exam_anxiety": [
        "anxiety",
        "stress",
        "nervous",
        "worried",
        "panic",
        "test anxiety",
        "exam stress",
    ],
    "adhd_focus": ["adhd", "attention", "focus", "concentration", "distract"],
}


def tag_post(title, selftext):
    """Apply rule-based tagging to a post."""
    text = f"{title} {selftext}".lower()
    tags = []

    for tag, keywords in TAG_RULES.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)

    return tags


def run_tagging(storage):
    """Tag all untagged posts."""
    posts = storage.get_posts_for_tagging()
    tagged_count = 0

    for post_id, title, selftext in posts:
        tags = tag_post(title or "", selftext or "")
        for tag in tags:
            storage.save_tag(post_id, tag)
        if tags:
            tagged_count += 1

    print(
        f"Tagged {tagged_count} posts with {sum(len(tag_post(p[1], p[2])) for p in posts)} tags"
    )

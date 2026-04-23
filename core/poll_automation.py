"""
Playwright-based poll creation in YouTube Studio Live Control Room.
Fails gracefully — any exception is caught and returned as an error string.
Selectors were discovered manually by inspecting YouTube Studio's DOM.
They may need updating if YouTube changes their UI.
"""
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# These selectors target the YouTube Studio Live Control Room polls interface.
# Update if YouTube redesigns their UI.
SELECTOR_POLLS_TAB = "button[aria-label*='Polls'], [data-testid='polls-tab']"
SELECTOR_CREATE_POLL = "button[aria-label*='Create poll'], yt-button-renderer:has-text('Create poll')"
SELECTOR_QUESTION_INPUT = "textarea[placeholder*='question'], input[placeholder*='question']"
SELECTOR_OPTION_INPUT = "input[placeholder*='option'], input[placeholder*='answer']"
SELECTOR_POST_POLL = "button[aria-label*='Post'], yt-button-renderer:has-text('Post')"

TIMEOUT_MS = 15_000


def create_poll(broadcast_id: str, question: str, options: list[str]) -> str | None:
    """
    Opens YouTube Studio Live Control Room for broadcast_id,
    creates a poll with the given question and options.
    Returns None on success, or an error message string on failure.
    """
    url = f"https://studio.youtube.com/video/{broadcast_id}/livestreaming"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            try:
                ctx = browser.new_context()
                page = ctx.new_page()

                page.goto(url, timeout=30_000)
                page.wait_for_load_state("networkidle", timeout=30_000)

                # Click the Polls tab
                page.click(SELECTOR_POLLS_TAB, timeout=TIMEOUT_MS)

                # Click Create poll
                page.click(SELECTOR_CREATE_POLL, timeout=TIMEOUT_MS)

                # Fill in the question
                page.fill(SELECTOR_QUESTION_INPUT, question, timeout=TIMEOUT_MS)

                # Wait for option inputs to render before querying
                page.wait_for_selector(SELECTOR_OPTION_INPUT, timeout=TIMEOUT_MS)
                option_inputs = page.query_selector_all(SELECTOR_OPTION_INPUT)
                for i, opt in enumerate(options):
                    if i < len(option_inputs):
                        option_inputs[i].fill(opt)
                    else:
                        # Click "Add option" to get another input field
                        add_btn = page.query_selector("button:has-text('Add option')")
                        if add_btn is None:
                            return f"Não foi possível adicionar a opção {i + 1}: botão 'Add option' não encontrado"
                        add_btn.click()
                        page.wait_for_selector(SELECTOR_OPTION_INPUT, timeout=TIMEOUT_MS)
                        option_inputs = page.query_selector_all(SELECTOR_OPTION_INPUT)
                        if i < len(option_inputs):
                            option_inputs[i].fill(opt)

                # Post the poll
                page.click(SELECTOR_POST_POLL, timeout=TIMEOUT_MS)
                page.wait_for_timeout(2_000)
            finally:
                browser.close()
        return None

    except PWTimeout as e:
        return f"Timeout ao criar enquete: {e}"
    except Exception as e:
        return f"Erro inesperado ao criar enquete: {e}"

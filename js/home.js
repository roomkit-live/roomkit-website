// Illustrative routing examples; no AI or messaging services are contacted.
const scenarios = {
    channels: {
        leftChannel: 'SMS',
        leftMessage: '“Can we talk about my order?”',
        leftCaption: 'A conversation begins.',
        rightChannel: 'Voice',
        rightMessage: '',
        rightCaption: 'Same person. Same conversation.',
        rightIcon: '#voice',
        agent: 'AI, in the loop',
        caption: 'Switch channels. Keep the context.',
    },
    human: {
        leftChannel: 'AI assistant',
        leftMessage: '“Let me bring in a teammate.”',
        leftCaption: 'Know when to hand things over.',
        rightChannel: 'Human teammate',
        rightMessage: '“I have the context. Let’s help.”',
        rightCaption: 'A handoff, without starting over.',
        rightIcon: '#message',
        agent: 'Everyone, on the same page',
        caption: 'Bring in a human. Keep the conversation.',
    },
    agents: {
        leftChannel: 'Researcher',
        leftMessage: '“Here’s what I found for you.”',
        leftCaption: 'One specialist finds the answer.',
        rightChannel: 'Writer',
        rightMessage: '“I’ll take it from here.”',
        rightCaption: 'The next turns it into a response.',
        rightIcon: '#spark',
        agent: 'A team, in one room',
        caption: 'Different specialists. Shared context.',
    },
};

const tabs = [...document.querySelectorAll('[data-scenario]')];
const panel = document.querySelector('#conversation-demo');
const fields = {
    leftChannel: '#left-channel',
    leftMessage: '#left-message',
    leftCaption: '#left-caption',
    rightChannel: '#right-channel',
    rightMessage: '#right-message',
    rightCaption: '#right-caption',
    agent: '#agent-label',
    caption: '#scenario-caption',
};
panel.setAttribute('role', 'tabpanel');
panel.setAttribute('aria-labelledby', tabs[0].id);
panel.tabIndex = 0;
document.querySelector('.demo-controls').hidden = false;

function selectScenario(tab, focus = false) {
    const scenario = scenarios[tab.dataset.scenario];
    tabs.forEach((item) => {
        item.setAttribute('aria-selected', String(item === tab));
        item.tabIndex = item === tab ? 0 : -1;
    });
    for (const [field, selector] of Object.entries(fields)) {
        document.querySelector(selector).textContent = scenario[field];
    }
    document.querySelector('#waveform').hidden = Boolean(scenario.rightMessage);
    document.querySelector('#right-message').hidden = !scenario.rightMessage;
    document.querySelector('#right-icon').setAttribute('href', scenario.rightIcon);
    panel.setAttribute('aria-labelledby', tab.id);
    if (focus) tab.focus();
}

tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectScenario(tab));
    tab.addEventListener('keydown', (event) => {
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = tabs.length - 1;
        if (next !== undefined) {
            event.preventDefault();
            selectScenario(tabs[next], true);
        }
    });
});

import { buildRows, stepIndex, swipeDirection, SWIPE_MIN_PX } from './lightboxNav';

const v = (id) => ({ id, aspect: 0.66 });
const h = (id) => ({ id, aspect: 1.5 });

describe('buildRows', () => {
    test('groups three verticals or two horizontals, interleaved', () => {
        const rows = buildRows([v('v1'), h('h1'), v('v2'), v('v3'), h('h2'), v('v4')]);
        expect(rows.map((r) => r.map((p) => p.id))).toEqual([
            ['v1', 'v2', 'v3'],
            ['h1', 'h2'],
            ['v4'],
        ]);
    });

    test('flattened rows are the on-screen order the lightbox steps through', () => {
        const rows = buildRows([h('h1'), v('v1'), h('h2'), h('h3')]);
        expect(rows.flat().map((p) => p.id)).toEqual(['v1', 'h1', 'h2', 'h3']);
    });

    test('missing aspect counts as horizontal', () => {
        expect(buildRows([{ id: 'x' }])).toEqual([[{ id: 'x' }]]);
    });
});

describe('stepIndex', () => {
    test('moves within range', () => {
        expect(stepIndex(1, 1, 3)).toBe(2);
        expect(stepIndex(1, -1, 3)).toBe(0);
    });
    test('stops at the ends instead of wrapping', () => {
        expect(stepIndex(2, 1, 3)).toBeNull();
        expect(stepIndex(0, -1, 3)).toBeNull();
    });
});

describe('swipeDirection', () => {
    test('finger moving left goes to the next photo', () => {
        expect(swipeDirection(-80, 10)).toBe(1);
    });
    test('finger moving right goes to the previous photo', () => {
        expect(swipeDirection(80, -10)).toBe(-1);
    });
    test('short moves and mostly-vertical moves are ignored', () => {
        expect(swipeDirection(SWIPE_MIN_PX - 1, 0)).toBe(0);
        expect(swipeDirection(-90, 120)).toBe(0);
    });
});

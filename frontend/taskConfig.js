// Task Configuration for PulseKey-aligned Assessment
const TASK_CONFIG = {
    tasks: [
        {
            id: 1,
            title: "Two-Pentagon Copy",
            instruction: "Copy the two-pentagon figure as accurately as possible using the reference image shown.",
            type: "reference-copy",
            referenceImage: "ReferanceImages/two-pentagon.png",
            duration: null, // No time limit
            hand: "both", // Can use either hand
            sequence: 1
        },
        {
            id: 2,
            title: "House Drawing Copy",
            instruction: "Copy the house drawing as accurately as possible using the reference image shown.",
            type: "reference-copy",
            referenceImage: "ReferanceImages/houseDrawing.png",
            duration: null,
            hand: "both",
            sequence: 2
        },
        {
            id: 3,
            title: "Clock Drawing",
            instruction: "Draw a clock face with numbers 1-12 and clock hands showing 10:10.",
            type: "freehand",
            referenceImage: "ReferanceImages/clock drawing.jpg",
            duration: null,
            hand: "both",
            sequence: 3
        },
        {
            id: 4,
            title: "Word Writing",
            instruction: "Write the word 'BIODEGRADABLE' in uppercase block letters.",
            type: "word-writing",
            prompt: "BIODEGRADABLE",
            duration: null,
            hand: "both",
            sequence: 4
        },
        {
            id: 5,
            title: "Cursive Sentence",
            instruction: "Write the sentence in cursive handwriting: 'The quick brown fox jumps beautifully'",
            type: "cursive-writing",
            prompt: "The quick brown fox jumps beautifully",
            duration: null,
            hand: "both",
            sequence: 5
        },
        {
            id: 6,
            title: "Loop Drawing - Right Hand",
            instruction: "Using your right hand, draw continuous loops for 5 seconds. The timer will start automatically when you begin drawing.",
            type: "timed-loop",
            duration: 5000, // 5 seconds in milliseconds
            hand: "right",
            sequence: 6
        },
        {
            id: 7,
            title: "Loop Drawing - Left Hand",
            instruction: "Using your left hand, draw continuous loops for 5 seconds. The timer will start automatically when you begin drawing.",
            type: "timed-loop",
            duration: 5000, // 5 seconds in milliseconds
            hand: "left",
            sequence: 7
        }
    ],

    getTaskById: function(id) {
        return this.tasks.find(t => t.id === id);
    },

    getTaskBySequence: function(sequence) {
        return this.tasks.find(t => t.sequence === sequence);
    },

    getTotalTasks: function() {
        return this.tasks.length;
    },

    getTaskIndex: function(id) {
        return this.tasks.findIndex(t => t.id === id);
    }
};

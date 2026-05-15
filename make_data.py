import json
# this script builds the catalog + student data and saves them to json files

catalog = {
    "courses": {
        "DS": {
            "name": "Data Structures",
            "type": "core",
            "credits": 3,
            "difficulty": 2,
            "prerequisites": [],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Smith",
                    "schedule": [
                        {"day": "Monday", "time": 9},
                        {"day": "Wednesday", "time": 9},
                        {"day": "Friday", "time": 9}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Johnson",
                    "schedule": [
                        {"day": "Tuesday", "time": 10},
                        {"day": "Thursday", "time": 10}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Williams",
                    "schedule": [
                        {"day": "Monday", "time": 14},
                        {"day": "Wednesday", "time": 14},
                        {"day": "Friday", "time": 14}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "ALG": {
            "name": "Algorithms",
            "type": "core",
            "credits": 3,
            "difficulty": 3,
            "prerequisites": ["DS"],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Brown",
                    "schedule": [
                        {"day": "Monday", "time": 11},
                        {"day": "Wednesday", "time": 11},
                        {"day": "Friday", "time": 11}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Davis",
                    "schedule": [
                        {"day": "Tuesday", "time": 13},
                        {"day": "Thursday", "time": 13}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Miller",
                    "schedule": [
                        {"day": "Monday", "time": 15},
                        {"day": "Wednesday", "time": 15},
                        {"day": "Friday", "time": 15}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "OS": {
            "name": "Operating Systems",
            "type": "core",
            "credits": 3,
            "difficulty": 3,
            "prerequisites": ["CA"],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Wilson",
                    "schedule": [
                        {"day": "Tuesday", "time": 9},
                        {"day": "Thursday", "time": 9}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Moore",
                    "schedule": [
                        {"day": "Monday", "time": 10},
                        {"day": "Wednesday", "time": 10},
                        {"day": "Friday", "time": 10}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Taylor",
                    "schedule": [
                        {"day": "Tuesday", "time": 15},
                        {"day": "Thursday", "time": 15}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "DB": {
            "name": "Database Systems",
            "type": "core",
            "credits": 3,
            "difficulty": 2,
            "prerequisites": ["DS"],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Anderson",
                    "schedule": [
                        {"day": "Monday", "time": 13},
                        {"day": "Wednesday", "time": 13},
                        {"day": "Friday", "time": 13}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Thomas",
                    "schedule": [
                        {"day": "Tuesday", "time": 11},
                        {"day": "Thursday", "time": 11}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Jackson",
                    "schedule": [
                        {"day": "Monday", "time": 16},
                        {"day": "Wednesday", "time": 16}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "CN": {
            "name": "Computer Networks",
            "type": "core",
            "credits": 3,
            "difficulty": 2,
            "prerequisites": ["OS"],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. White",
                    "schedule": [
                        {"day": "Tuesday", "time": 8},
                        {"day": "Thursday", "time": 8}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Harris",
                    "schedule": [
                        {"day": "Monday", "time": 12},
                        {"day": "Wednesday", "time": 12},
                        {"day": "Friday", "time": 12}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Martin",
                    "schedule": [
                        {"day": "Tuesday", "time": 14},
                        {"day": "Thursday", "time": 14}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "SE": {
            "name": "Software Engineering",
            "type": "core",
            "credits": 3,
            "difficulty": 2,
            "prerequisites": [],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Thompson",
                    "schedule": [
                        {"day": "Monday", "time": 8},
                        {"day": "Wednesday", "time": 8},
                        {"day": "Friday", "time": 8}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Garcia",
                    "schedule": [
                        {"day": "Tuesday", "time": 12},
                        {"day": "Thursday", "time": 12}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Martinez",
                    "schedule": [
                        {"day": "Monday", "time": 17},
                        {"day": "Wednesday", "time": 17}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "CA": {
            "name": "Computer Architecture",
            "type": "core",
            "credits": 3,
            "difficulty": 3,
            "prerequisites": [],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Robinson",
                    "schedule": [
                        {"day": "Tuesday", "time": 16},
                        {"day": "Thursday", "time": 16}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Clark",
                    "schedule": [
                        {"day": "Monday", "time": 8},
                        {"day": "Wednesday", "time": 8},
                        {"day": "Friday", "time": 8}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Rodriguez",
                    "schedule": [
                        {"day": "Tuesday", "time": 14},
                        {"day": "Thursday", "time": 14}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "TC": {
            "name": "Theory of Computation",
            "type": "core",
            "credits": 3,
            "difficulty": 3,
            "prerequisites": ["ALG"],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Lewis",
                    "schedule": [
                        {"day": "Monday", "time": 10},
                        {"day": "Wednesday", "time": 10},
                        {"day": "Friday", "time": 10}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Lee",
                    "schedule": [
                        {"day": "Tuesday", "time": 15},
                        {"day": "Thursday", "time": 15}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Walker",
                    "schedule": [
                        {"day": "Monday", "time": 16},
                        {"day": "Wednesday", "time": 16},
                        {"day": "Friday", "time": 16}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "ML": {
            "name": "Machine Learning",
            "type": "elective",
            "credits": 3,
            "difficulty": 3,
            "prerequisites": ["ALG"],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Hall",
                    "schedule": [
                        {"day": "Tuesday", "time": 10},
                        {"day": "Thursday", "time": 10}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Allen",
                    "schedule": [
                        {"day": "Monday", "time": 14},
                        {"day": "Wednesday", "time": 14},
                        {"day": "Friday", "time": 14}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Young",
                    "schedule": [
                        {"day": "Tuesday", "time": 13},
                        {"day": "Thursday", "time": 13}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "GD": {
            "name": "Game Development",
            "type": "elective",
            "credits": 3,
            "difficulty": 2,
            "prerequisites": ["DS"],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Adams",
                    "schedule": [
                        {"day": "Monday", "time": 15},
                        {"day": "Wednesday", "time": 15},
                        {"day": "Friday", "time": 15}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Baker",
                    "schedule": [
                        {"day": "Tuesday", "time": 8},
                        {"day": "Thursday", "time": 8}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Gonzalez",
                    "schedule": [
                        {"day": "Monday", "time": 10},
                        {"day": "Wednesday", "time": 10}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        },
        "MAD": {
            "name": "Mobile App Development",
            "type": "elective",
            "credits": 3,
            "difficulty": 2,
            "prerequisites": ["SE"],
            "sections": [
                {
                    "section_id": 1,
                    "professor": "Dr. Nelson",
                    "schedule": [
                        {"day": "Tuesday", "time": 14},
                        {"day": "Thursday", "time": 14}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 2,
                    "professor": "Dr. Carter",
                    "schedule": [
                        {"day": "Monday", "time": 11},
                        {"day": "Wednesday", "time": 11},
                        {"day": "Friday", "time": 11}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                },
                {
                    "section_id": 3,
                    "professor": "Dr. Mitchell",
                    "schedule": [
                        {"day": "Tuesday", "time": 17},
                        {"day": "Thursday", "time": 17}
                    ],
                    "capacity": 30,
                    "enrolled": 0
                }
            ]
        }
    },
    "time_slots": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "difficulty_levels": {
        "1": "Easy",
        "2": "Medium",
        "3": "Hard"
    }
}

# student data: who needs what and their preferences
students_data = {
    "students": {
        "S1": {
            "name": "Student 1",
            "year": 3,
            "required_credits": 15,
            "required_courses": {
                "core": ["ALG", "OS", "DB", "TC"],
                "electives": 1,
                "elective_pool": ["GD", "MAD"]
            },
            "completed_courses": ["CA", "SE", "DS"],
            "time_preferences": {
                "preferred": {
                    "description": "Morning person",
                    "time_slots": [8, 9, 10, 11]
                },
                "blocked": {
                    "description": "Part-time job Wed/Fri 4-6PM",
                    "slots": [
                        {"day": "Wednesday", "time": 16},
                        {"day": "Wednesday", "time": 17},
                        {"day": "Friday", "time": 16},
                        {"day": "Friday", "time": 17}
                    ]
                }
            },
            "friends": ["S3"],
            "max_courses_per_day": 3
        },
        "S2": {
            "name": "Student 2",
            "year": 4,
            "required_credits": 15,
            "required_courses": {
                "core": ["CN", "TC"],
                "electives": 3,
                "elective_pool": ["ML", "GD", "MAD"]
            },
            "completed_courses": ["DS", "ALG", "OS", "DB", "SE", "CA"],
            "time_preferences": {
                "preferred": {
                    "description": "Afternoon person",
                    "time_slots": [12, 13, 14, 15]
                },
                "blocked": {
                    "description": "No blocked times",
                    "slots": []
                }
            },
            "special_constraints": {
                "minimize_gaps": True,
                "description": "Commuter"
            },
            "friends": ["S4"],
            "max_courses_per_day": 3
        },
        "S3": {
            "name": "Student 3",
            "year": 3,
            "required_credits": 15,
            "required_courses": {
                "core": ["ALG", "OS", "DB", "CN", "TC"],
                "electives": 0,
                "elective_pool": []
            },
            "completed_courses": ["CA", "SE", "DS"],
            "time_preferences": {
                "preferred": {
                    "description": "Flexible",
                    "time_slots": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
                },
                "blocked": {
                    "description": "No blocked times",
                    "slots": []
                }
            },
            "friends": ["S1", "S5"],
            "max_courses_per_day": 3
        },
        "S4": {
            "name": "Student 4",
            "year": 2,
            "required_credits": 15,
            "required_courses": {
                "core": ["DS", "CA", "SE"],
                "electives": 2,
                "elective_pool": ["GD", "MAD"]
            },
            "completed_courses": [],
            "time_preferences": {
                "preferred": {
                    "description": "Morning person",
                    "time_slots": [8, 9, 10, 11]
                },
                "blocked": {
                    "description": "Sports Mon/Wed/Fri 2-4PM",
                    "slots": [
                        {"day": "Monday", "time": 14},
                        {"day": "Monday", "time": 15},
                        {"day": "Wednesday", "time": 14},
                        {"day": "Wednesday", "time": 15},
                        {"day": "Friday", "time": 14},
                        {"day": "Friday", "time": 15}
                    ]
                }
            },
            "friends": ["S2"],
            "max_courses_per_day": 3
        },
        "S5": {
            "name": "Student 5",
            "year": 3,
            "required_credits": 15,
            "required_courses": {
                "core": ["ALG", "DB", "SE", "CN"],
                "electives": 1,
                "elective_pool": ["GD", "MAD"]
            },
            "completed_courses": ["CA", "OS", "DS"],
            "time_preferences": {
                "preferred": {
                    "description": "Late afternoon",
                    "time_slots": [14, 15, 16, 17]
                },
                "blocked": {
                    "description": "Penalty for 8AM",
                    "slots": []
                }
            },
            "special_constraints": {
                "avoid_early": True,
                "penalty_time": 8
            },
            "friends": ["S3"],
            "max_courses_per_day": 3
        }
    },
    "friend_pairs": [["S1", "S3"], ["S2", "S4"], ["S3", "S5"]],
    "global_constraints": {
        "lunch_time": {
            "time_slot": 12,
            "preferred_days_free": 3
        },
        "max_courses_per_day": 3,
        "min_gap_minutes": 0,
        "max_gap_hours": 4
    }
}


def write_json_file(filename, data):
    """simple helper to save a dict as json"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


# write both json files and print a small message
write_json_file("course_catalog.json", catalog)
write_json_file("student_requirements.json", students_data)
print("Data files created successfully")
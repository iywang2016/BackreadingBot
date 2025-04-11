import logging
import os
import re

from collections import defaultdict

from src.ed_helper import EdHelper

from typing import (
    List, Optional, Callable, Dict
)

from src.constants import (
    PROGRESS_UPDATE_MULTIPLE
)

class DeductionsRegex:
    GENERAL_DEDUCTIONS_PATTERN = re.compile(r'.*General Deductions:\s*')
    CREATIVE_EXTENSION_PATTERN = re.compile(r'Creative Extension:\s*')
    TESTING_REFLECTION_PATTERN = re.compile(r'Testing/Reflection:.*')

class DeductionsChecker:
    @staticmethod
    async def check_deductions(
        ed_helper: EdHelper,
        url: str, file_name: str,
        template: Optional[bool] = False,
        progress_bar_update: Optional[Callable[[int, int], None]] = None,
        ferpa: Optional[bool] = True
    ) -> Dict[str, int]:
        # Get List[str] where each element is a string of one student's
        # final feedback box
        feedback_list = await DeductionsChecker._pull_submissions(ed_helper, url, template, progress_bar_update, ferpa)

        # Parse final feedback box List[str]s into a List where each
        # element is a string representation a deduction bullet point

        # Group all deduction lines into a Dict
        
        return

    @staticmethod
    async def _pull_submissions(
        ed_helper: EdHelper,
        url: str,
        template: Optional[bool] = False,
        progress_bar_update: Optional[Callable[[int, int], None]] = None,
        ferpa: Optional[bool] = True
    ) -> List[str]:
        """
        Pulls final submission slides of all student submissions and creates
        a List with all the contents of each feedback box.

        Params: 'ed_helper' - A properly initialized EdHelper object with API
                              access to the ed assignment
                'url' - The ed assignment url
                'template' - Whether or not the grading template is expected,
                             default False
                'progress_bar_update' - A function to call with incremental
                                        values that updates a user-viewable
                                        progress bar, default None
                'ferpa' - Whether or not to censor student emails from links,
                          default True
        Returns: A dictionary mapping (TA | link) -> (link, fixes) for all
                 assignment that had incorrect formatting and a List of links
                 to student assignments not found in the grading spreadsheet
        """
        attempt_slide = EdHelper.is_overall_submission_link(url)

        # Get the challenge id for the assignment
        ids = EdHelper.get_ids(url)
        lesson_id, slide_id = ids[1], ids[2]
        challenge_id = (ed_helper.get_slide(url)['challenge_id']
                        if not attempt_slide else None)

        # Get user/challenge information
        users, num_criteria, rubric = None, None, None
        if not attempt_slide:
            users = [(user['id'], None, user['tutorial'], None)
                     for user in ed_helper.get_challenge_users(challenge_id)
                     if user['course_role'] == "student"]

            challenge = ed_helper.get_challenge(challenge_id)
            num_criteria = len(challenge['settings']['criteria'])
        else:
            users = [(attempt['user_id'], attempt['email'],
                      attempt['tutorial'], attempt['sourced_id'])
                     for attempt in ed_helper.get_attempt_results(lesson_id)
                     if attempt['course_role'] == 'student']

            lesson = ed_helper.get_lesson(lesson_id)
            rubric = ed_helper.get_rubric(ed_helper.get_rubric_id(slide_id))
            num_criteria = len(rubric['sections'])

        feedback_list, count = [], 0

        for (user_id, email, section, submission_id) in users:
            if count % PROGRESS_UPDATE_MULTIPLE == 0:
                if progress_bar_update is not None:
                    _ = await progress_bar_update(count, len(users))
                logging.info(f"{count} / {len(users)} Completed")
            count += 1

            submissions = (ed_helper.get_challenge_submissions(
                                user_id, challenge_id
                           ) if not attempt_slide else
                           ed_helper.get_attempt_submissions(
                                user_id, lesson_id, slide_id,
                                submission_id, rubric
                           ))
            # Get all text from final submission box
            if submissions is None:
                continue
            final_submission = submissions[0]
            if final_submission is None:
                continue
            feedback_list.append(submissions[0]['feedback']['content'])
        
        print(feedback_list)
        return feedback_list
    
    @staticmethod
    async def _get_deduction_lines(
        feedback_list: List[str]
    ) -> List[str]:
        # For creative: take everything between "General Deductions:", "Creative Extension:"
        # "Testing/Reflection:"
        deduction_lines = []
        for feedback in feedback_list:
            trim_gen_deductions = re.sub(DeductionsRegex.GENERAL_DEDUCTIONS_PATTERN, '',
                                         feedback)
            trim_creative_ext = re.sub(DeductionsRegex.CREATIVE_EXTENSION_PATTERN, '',
                                       trim_gen_deductions)
            trim_reflection = re.sub(DeductionsRegex.TESTING_REFLECTION_PATTERN, '',
                                     trim_creative_ext)
            deduction_lines.append(trim_reflection)
        
        print(deduction_lines)
        return deduction_lines
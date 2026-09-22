export interface MockReview {
  id: string;
  platform: "Amazon" | "Reddit";
  category: "negative" | "positive" | "neutral";
  theme: string;
  title: string;
  author: string;
  date?: string;
  rating?: number;
  subreddit?: string;
  content: string;
}

export interface ReviewCollection {
  platform: "Amazon" | "Reddit";
  category: "negative" | "positive" | "neutral";
  theme: string;
  markdown: string;
  reviews: MockReview[];
}

/**
 * Reviews for Amazon - negative - not using the product
 */
export const reviewsAmazonNegativeNotUsing: ReviewCollection = {
  platform: "Amazon",
  category: "negative",
  theme: "not using the product",
  markdown: `## Amazon - Negative - Not using the product

### Review 1:
**Rating:** 2/5 stars
**Title:** Sitting unopened on my nightstand — too paralyzed by shame to even start
Bought this book during a late-night panic attack hoping it would be the lifeline I desperately needed. I quit my job due to extreme anxiety and haven't worked for the past 6 months. I feel extreme shame about it, like I'm a failure.
I opened the book, read through the introduction, and immediately hit a wall. Chapter 1 tells you to "audit your career achievements" and "reach out to former colleagues for coffees." I couldn't even finish the chapter. Right now, shame has been a heavy burden on my heart. I’m overwhelmed with shame, and the only thing worse than not working is not knowing how to answer the question, “What do you do for a living?”
The thought of reaching out to people while I feel this way made my stomach turn. I closed the cover and it’s been sitting on my nightstand ever since, taunting me. If you’re already drowning in self-blame, this book expects a level of baseline confidence and emotional stability that someone in my position simply doesn't have. It might be great if you're just bored at work, but if you're truly in the pit, it just sits there unread.

### Review 2:
**Rating:** 1/5 stars
**Title:** Could not get past chapter 2 — tone-deaf to real despair
I work in sales. For the longest time, I was successful. Last year, out of nowhere, I was put on an action plan because of poor performance. I felt so much shame that I was close to suicide.
Someone recommended this program to help me rebuild. I bought the physical workbook and audio companion. But listening to the author's relentless "go-getter" cheerfulness felt like a slap in the face. Even my therapist seems sick of hearing about how much of a loser I feel like. “You’re catastrophizing,” she said. But can you really catastrophize something that has already happened? What do you say to someone in their mid-twenties, with no career to speak of, living in the attic of their parents’ house? “Everything is going to be okay”? That sounds hollow.
I haven’t touched the materials in two months. The workbook is in a drawer, untouched. It just triggered more feelings of worthlessness and shame. I couldn't bring myself to do the exercises.

### Review 3:
**Rating:** 2/5 stars
**Title:** Another thing I purchased and couldn't bring myself to finish
I’m on medical leave for depression right now, and I’m terrified of my peers finding out. I’ve felt an immense amount of shame. It’s hard to shake the feeling of failure.
I purchased this guide hoping for gentle, practical steps to help rebuild my career confidence. Instead, from the first few pages, i felt shame, self-hatred, and anxiety rushing back in. The book demands immediate momentum—setting up informational interviews, pitching yourself, networking. When you can barely face your family, how are you supposed to sell yourself to strangers?
I stopped reading after page 40. Now it's just another reminder on my shelf of something I failed to follow through on. I’m deeply ashamed of how my career turned out. I could’ve done better, had higher self-esteem, taken more risks, etc., but this book assumes you're already in a headspace to take action. It didn't meet me where I was at.

### Review 4:
**Rating:** 1/5 stars
**Title:** Not for people who are genuinely struggling
I was recently terminated for cause due to performance issues. I feel like a massive failure and I don’t know how to move forward. The feelings of worthlessness and shame are overwhelming.
I bought this hoping for a realistic blueprint for recovery. What I got was standard corporate pep-talk disguised as deep advice. I tried doing the self-reflection prompts, but I’m ashamed of my career, but I feel powerless to change it.
I gave up on the third chapter and filed for a return, but missed the return window. It is now collecting dust. If you are dealing with genuine career trauma or depression, this will likely sit abandoned like it did for me.
`,
  reviews: [
    {
      id: "amzn-neg-1",
      platform: "Amazon",
      category: "negative",
      theme: "not using the product",
      rating: 2,
      title: "Sitting unopened on my nightstand — too paralyzed by shame to even start",
      author: "Verified Purchaser",
      date: "2 months ago",
      content: `Bought this book during a late-night panic attack hoping it would be the lifeline I desperately needed. I quit my job due to extreme anxiety and haven't worked for the past 6 months. I feel extreme shame about it, like I'm a failure.
I opened the book, read through the introduction, and immediately hit a wall. Chapter 1 tells you to "audit your career achievements" and "reach out to former colleagues for coffees." I couldn't even finish the chapter. Right now, shame has been a heavy burden on my heart. I’m overwhelmed with shame, and the only thing worse than not working is not knowing how to answer the question, “What do you do for a living?”
The thought of reaching out to people while I feel this way made my stomach turn. I closed the cover and it’s been sitting on my nightstand ever since, taunting me. If you’re already drowning in self-blame, this book expects a level of baseline confidence and emotional stability that someone in my position simply doesn't have. It might be great if you're just bored at work, but if you're truly in the pit, it just sits there unread.`
    },
    {
      id: "amzn-neg-2",
      platform: "Amazon",
      category: "negative",
      theme: "not using the product",
      rating: 1,
      title: "Could not get past chapter 2 — tone-deaf to real despair",
      author: "Verified Purchaser",
      date: "3 weeks ago",
      content: `I work in sales. For the longest time, I was successful. Last year, out of nowhere, I was put on an action plan because of poor performance. I felt so much shame that I was close to suicide.
Someone recommended this program to help me rebuild. I bought the physical workbook and audio companion. But listening to the author's relentless "go-getter" cheerfulness felt like a slap in the face. Even my therapist seems sick of hearing about how much of a loser I feel like. “You’re catastrophizing,” she said. But can you really catastrophize something that has already happened? What do you say to someone in their mid-twenties, with no career to speak of, living in the attic of their parents’ house? “Everything is going to be okay”? That sounds hollow.
I haven’t touched the materials in two months. The workbook is in a drawer, untouched. It just triggered more feelings of worthlessness and shame. I couldn't bring myself to do the exercises.`
    },
    {
      id: "amzn-neg-3",
      platform: "Amazon",
      category: "negative",
      theme: "not using the product",
      rating: 2,
      title: "Another thing I purchased and couldn't bring myself to finish",
      author: "Verified Purchaser",
      date: "1 month ago",
      content: `I’m on medical leave for depression right now, and I’m terrified of my peers finding out. I’ve felt an immense amount of shame. It’s hard to shake the feeling of failure.
I purchased this guide hoping for gentle, practical steps to help rebuild my career confidence. Instead, from the first few pages, i felt shame, self-hatred, and anxiety rushing back in. The book demands immediate momentum—setting up informational interviews, pitching yourself, networking. When you can barely face your family, how are you supposed to sell yourself to strangers?
I stopped reading after page 40. Now it's just another reminder on my shelf of something I failed to follow through on. I’m deeply ashamed of how my career turned out. I could’ve done better, had higher self-esteem, taken more risks, etc., but this book assumes you're already in a headspace to take action. It didn't meet me where I was at.`
    },
    {
      id: "amzn-neg-4",
      platform: "Amazon",
      category: "negative",
      theme: "not using the product",
      rating: 1,
      title: "Not for people who are genuinely struggling",
      author: "Verified Purchaser",
      date: "4 months ago",
      content: `I was recently terminated for cause due to performance issues. I feel like a massive failure and I don’t know how to move forward. The feelings of worthlessness and shame are overwhelming.
I bought this hoping for a realistic blueprint for recovery. What I got was standard corporate pep-talk disguised as deep advice. I tried doing the self-reflection prompts, but I’m ashamed of my career, but I feel powerless to change it.
I gave up on the third chapter and filed for a return, but missed the return window. It is now collecting dust. If you are dealing with genuine career trauma or depression, this will likely sit abandoned like it did for me.`
    }
  ]
};

/**
 * Reviews for Reddit - negative - not using the product
 */
export const reviewsRedditNegativeNotUsing: ReviewCollection = {
  platform: "Reddit",
  category: "negative",
  theme: "not using the product",
  markdown: `## Reddit - Negative - Not using the product

### Post / Comment 1:
**Subreddit:** r/careerguidance
**Title:** Bought the program 3 months ago, haven't touched it since week 1. Anyone else just paralyzed by shame?
Has anyone else bought this course and completely abandoned it? I bought it right after getting fired. I was recently terminated for cause due to performance issues, and I feel like a massive failure. I don't know how to move forward—the feelings of worthlessness and shame are overwhelming.
When I signed up, I thought it would hold my hand through the process of getting back on my feet. But the very first module tells you to reach out to your network and update your LinkedIn profile. I literally broke down in tears. Shame is the primary feeling. The only thing worse than not working is not knowing how to answer the question, “What do you do for a living?”
I haven't logged in for 9 weeks. I get the automated reminder emails telling me I'm behind on the modules, and each notification just triggers another wave of guilt. I felt shame, self-hatred, and anxiety before, and now I have the added shame of spending money on a course I can't even stomach opening.

### Post / Comment 2:
**Subreddit:** r/jobs
**Title:** Can't bring myself to open this book. What do you do when the advice feels completely hollow?
A friend sent me a copy after I told them I quit my job due to extreme anxiety and haven't worked for the past 6 months. I feel extreme shame about it, like I'm a failure.
I really tried to engage with it. I sat down with a highlighter and notebook. But the whole premise seems to be based on the idea that you're just "temporarily between roles" or "recalibrating." It does nothing to address the raw, visceral self-hatred when you feel like your life is over. Even my therapist seems sick of hearing about how much of a loser I feel like. “You’re catastrophizing,” she said. But can you really catastrophize something that has already happened? What do you say to someone in their mid-twenties, with no career to speak of, living in the attic of their parents’ house? “Everything is going to be okay”? That sounds hollow.
I closed the book, shoved it under my bed, and haven't looked at it since. It's impossible to use career advice when you can't even get past the shame of existing.

### Post / Comment 3:
**Subreddit:** r/decidingtobebetter
**Title:** Comment on: "Did anyone actually complete the modules?"
Nope. Paid full price, watched half of the first video, and abandoned it.
I’m on medical leave for depression right now, and I’m terrified of my peers finding out. I’ve felt an immense amount of shame. It’s hard to shake the feeling of failure.
The instructor hops on screen with this high-energy, cheerful demeanor talking about "unlocking your potential" and "owning your narrative." I felt so alienated.
I’m deeply ashamed of how my career turned out. I could’ve done better, had higher self-esteem, taken more risks, etc. Shame has been a heavy burden on my heart. I’m overwhelmed with shame just thinking about my resume gap.
Seeing everyone in the course Slack sharing their "wins" made me feel a thousand times worse. I logged out, muted notifications, and haven't touched it. Just another expensive guilt trip.

### Post / Comment 4:
**Subreddit:** r/sales
**Title:** Put on a PIP, bought a career turnaround guide, haven't opened it once
I work in sales. For the longest time, I was successful. Last year, out of nowhere, I was put on an action plan because of poor performance. I felt so much shame that I was close to suicide.
In a moment of desperation I bought this highly recommended career recovery program. It’s been sitting in my browser bookmarks untouched for over 4 months. Every time I think about logging in, my chest tightens. I’m ashamed of my career, but I feel powerless to change it.
The worst part is that the program assumes you have the mental bandwidth to start cold messaging recruiters and rebuilding your pipeline. When you're carrying around this much shame, your brain is just in survival mode. The product is probably fine for someone who just had a minor setback, but for anyone who is genuinely broken, it’s completely unusable. Total waste of money for me.
`,
  reviews: [
    {
      id: "reddit-neg-1",
      platform: "Reddit",
      category: "negative",
      theme: "not using the product",
      subreddit: "r/careerguidance",
      title: "Bought the program 3 months ago, haven't touched it since week 1. Anyone else just paralyzed by shame?",
      author: "u/anxious_jobseeker99",
      date: "3 months ago",
      content: `Has anyone else bought this course and completely abandoned it? I bought it right after getting fired. I was recently terminated for cause due to performance issues, and I feel like a massive failure. I don't know how to move forward—the feelings of worthlessness and shame are overwhelming.
When I signed up, I thought it would hold my hand through the process of getting back on my feet. But the very first module tells you to reach out to your network and update your LinkedIn profile. I literally broke down in tears. Shame is the primary feeling. The only thing worse than not working is not knowing how to answer the question, “What do you do for a living?”
I haven't logged in for 9 weeks. I get the automated reminder emails telling me I'm behind on the modules, and each notification just triggers another wave of guilt. I felt shame, self-hatred, and anxiety before, and now I have the added shame of spending money on a course I can't even stomach opening.`
    },
    {
      id: "reddit-neg-2",
      platform: "Reddit",
      category: "negative",
      theme: "not using the product",
      subreddit: "r/jobs",
      title: "Can't bring myself to open this book. What do you do when the advice feels completely hollow?",
      author: "u/lostinmy20s_throwaway",
      date: "1 month ago",
      content: `A friend sent me a copy after I told them I quit my job due to extreme anxiety and haven't worked for the past 6 months. I feel extreme shame about it, like I'm a failure.
I really tried to engage with it. I sat down with a highlighter and notebook. But the whole premise seems to be based on the idea that you're just "temporarily between roles" or "recalibrating." It does nothing to address the raw, visceral self-hatred when you feel like your life is over. Even my therapist seems sick of hearing about how much of a loser I feel like. “You’re catastrophizing,” she said. But can you really catastrophize something that has already happened? What do you say to someone in their mid-twenties, with no career to speak of, living in the attic of their parents’ house? “Everything is going to be okay”? That sounds hollow.
I closed the book, shoved it under my bed, and haven't looked at it since. It's impossible to use career advice when you can't even get past the shame of existing.`
    },
    {
      id: "reddit-neg-3",
      platform: "Reddit",
      category: "negative",
      theme: "not using the product",
      subreddit: "r/decidingtobebetter",
      title: "Comment on: 'Did anyone actually complete the modules?'",
      author: "u/shadow_cast_91",
      date: "2 weeks ago",
      content: `Nope. Paid full price, watched half of the first video, and abandoned it.
I’m on medical leave for depression right now, and I’m terrified of my peers finding out. I’ve felt an immense amount of shame. It’s hard to shake the feeling of failure.
The instructor hops on screen with this high-energy, cheerful demeanor talking about "unlocking your potential" and "owning your narrative." I felt so alienated.
I’m deeply ashamed of how my career turned out. I could’ve done better, had higher self-esteem, taken more risks, etc. Shame has been a heavy burden on my heart. I’m overwhelmed with shame just thinking about my resume gap.
Seeing everyone in the course Slack sharing their "wins" made me feel a thousand times worse. I logged out, muted notifications, and haven't touched it. Just another expensive guilt trip.`
    },
    {
      id: "reddit-neg-4",
      platform: "Reddit",
      category: "negative",
      theme: "not using the product",
      subreddit: "r/sales",
      title: "Put on a PIP, bought a career turnaround guide, haven't opened it once",
      author: "u/exhausted_closer",
      date: "3 weeks ago",
      content: `I work in sales. For the longest time, I was successful. Last year, out of nowhere, I was put on an action plan because of poor performance. I felt so much shame that I was close to suicide.
In a moment of desperation I bought this highly recommended career recovery program. It’s been sitting in my browser bookmarks untouched for over 4 months. Every time I think about logging in, my chest tightens. I’m ashamed of my career, but I feel powerless to change it.
The worst part is that the program assumes you have the mental bandwidth to start cold messaging recruiters and rebuilding your pipeline. When you're carrying around this much shame, your brain is just in survival mode. The product is probably fine for someone who just had a minor setback, but for anyone who is genuinely broken, it’s completely unusable. Total waste of money for me.`
    }
  ]
};

export const allMockReviews = [
  reviewsAmazonNegativeNotUsing,
  reviewsRedditNegativeNotUsing,
];

export default allMockReviews;

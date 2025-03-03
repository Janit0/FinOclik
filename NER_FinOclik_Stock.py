#!/usr/bin/env python
# coding: utf-8

# In[1]:





# In[36]:


organization_list = ["AAPL", "Google", "IBM", "AMZN"]

    def extract_organization(sentence, organization_list):
        # Tokenize the sentence
        tokens = word_tokenize(sentence)
    
        # Perform part-of-speech tagging
        pos_tags = pos_tag(tokens)
    
        # Perform named entity recognition
        named_entities = ne_chunk(pos_tags)

    # Extract organization names
    organization_names = []
    for entity in named_entities:
        if isinstance(entity, nltk.tree.Tree) and entity.label() == 'ORGANIZATION':
            org_name = ' '.join([leaf[0] for leaf in entity.leaves()])
            if org_name in organization_list:
                organization_names.append(org_name)

    return organization_names

# Example usage:
sentence = "AAPL has different stocks"
organization_names = extract_organization(sentence, organization_list)
print("Organization name(s):", organization_names)


# In[37]:



# In[ ]:





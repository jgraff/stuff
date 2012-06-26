#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "list.h"

void test__ADT_sl_list_push()
{
  struct ADT_sl_list *list = (struct ADT_sl_list *)malloc(sizeof(struct ADT_sl_list));
  char *a_ptr = (char *)malloc(sizeof(char));
  assert(list != NULL);

  *a_ptr = 'a';

  ADT_sl_list_init(list);
  ADT_sl_list_push(list, a_ptr);
  assert(*(char *)list->head->data == 'a');
  printf("Test Single Linked List Push (ADT_sl_list_push)...ok\n");
  ADT_sl_list_destroy(list, &free);
  free(list);
}

void test__ADT_sl_list_pop()
{
  struct ADT_sl_list *list = (struct ADT_sl_list *)malloc(sizeof(struct ADT_sl_list));
  char *a_ptr = (char *)malloc(sizeof(char));
  char *tmp;
  assert(list != NULL);

  *a_ptr = 'a';

  ADT_sl_list_init(list);
  ADT_sl_list_push(list, a_ptr);
  ADT_sl_list_pop(list, (void *)&tmp);
  assert(*(char *)tmp == 'a');
  free(tmp);
  printf("Test Single Linked List Pop (ADT_sl_list_pop)...ok\n");
  ADT_sl_list_destroy(list, &free);
  free(list);
}

void test__ADT_sl_list_append()
{
  struct ADT_sl_list *list = (struct ADT_sl_list *)malloc(sizeof(struct ADT_sl_list));
  char *a_ptr = (char *)malloc(sizeof(char));
  char *b_ptr = (char *)malloc(sizeof(char));
  assert(list != NULL);

  *a_ptr = 'a';
  *b_ptr = 'b';

  ADT_sl_list_init(list);
  /* Do multiple appends since the first append is actually a push. */
  ADT_sl_list_append(list, a_ptr);
  ADT_sl_list_append(list, b_ptr);
  assert(*(char *)list->head->next->data == 'b');
  printf("Test Single Linked List Append (ADT_sl_list_append)...ok\n");
  ADT_sl_list_destroy(list, &free);
  free(list);
}

void test__ADT_sl_list_insert_after()
{
  struct ADT_sl_list *list = (struct ADT_sl_list *)malloc(sizeof(struct ADT_sl_list));
  char *a_ptr = (char *)malloc(sizeof(char));
  char *b_ptr = (char *)malloc(sizeof(char));
  assert(list != NULL);

  *a_ptr = 'a';
  *b_ptr = 'b';

  ADT_sl_list_init(list);
  ADT_sl_list_push(list, a_ptr);
  ADT_sl_list_insert_after(list, list->head, b_ptr);
  assert(*(char *)list->head->next->data == 'b');
  printf("Test Single Linked List Insert After (ADT_sl_list_insert_after)...ok\n");
  ADT_sl_list_destroy(list, &free);
  free(list);
}

void test__ADT_sl_list_remove_after()
{
  struct ADT_sl_list *list = (struct ADT_sl_list *)malloc(sizeof(struct ADT_sl_list));
  char *a_ptr = (char *)malloc(sizeof(char));
  char *b_ptr = (char *)malloc(sizeof(char));
  char *tmp;
  assert(list != NULL);

  *a_ptr = 'a';
  *b_ptr = 'b';

  ADT_sl_list_init(list);
  ADT_sl_list_append(list, a_ptr);
  ADT_sl_list_append(list, b_ptr);
  ADT_sl_list_remove_after(list, list->head, (void *)&tmp);
  assert(*(char *)tmp == 'b');
  free(tmp);
  printf("Test Single Linked List Remove After (ADT_sl_list_remove_after)...ok\n");
  ADT_sl_list_destroy(list, &free);
  free(list);
}

void test__ADT_sl_list_length()
{
  struct ADT_sl_list *list = (struct ADT_sl_list *)malloc(sizeof(struct ADT_sl_list));
  char *a_ptr = (char *)malloc(sizeof(char));
  char *b_ptr = (char *)malloc(sizeof(char));
  char *c_ptr = (char *)malloc(sizeof(char));
  char *d_ptr = (char *)malloc(sizeof(char));
  char *e_ptr = (char *)malloc(sizeof(char));
  char *f_ptr = (char *)malloc(sizeof(char));
  char *tmp;
  assert(list != NULL);

  *a_ptr = 'a';
  *b_ptr = 'b';
  *c_ptr = 'c';
  *d_ptr = 'd';
  *e_ptr = 'e';
  *f_ptr = 'f';

  /* count up */
  ADT_sl_list_init(list);
  assert(ADT_sl_list_length(list) == 0);
  ADT_sl_list_append(list, a_ptr);
  assert(ADT_sl_list_length(list) == 1);
  ADT_sl_list_append(list, b_ptr);
  assert(ADT_sl_list_length(list) == 2);
  ADT_sl_list_append(list, c_ptr);
  assert(ADT_sl_list_length(list) == 3);
  ADT_sl_list_append(list, d_ptr);
  assert(ADT_sl_list_length(list) == 4);
  ADT_sl_list_append(list, e_ptr);
  assert(ADT_sl_list_length(list) == 5);
  ADT_sl_list_append(list, f_ptr);
  assert(ADT_sl_list_length(list) == 6);

  /* count down */
  ADT_sl_list_pop(list, (void *)&tmp);
  free(tmp);
  assert(ADT_sl_list_length(list) == 5);
  ADT_sl_list_pop(list, (void *)&tmp);
  free(tmp);
  assert(ADT_sl_list_length(list) == 4);
  ADT_sl_list_pop(list, (void *)&tmp);
  free(tmp);
  assert(ADT_sl_list_length(list) == 3);
  ADT_sl_list_pop(list, (void *)&tmp);
  free(tmp);
  assert(ADT_sl_list_length(list) == 2);
  ADT_sl_list_pop(list, (void *)&tmp);
  free(tmp);
  assert(ADT_sl_list_length(list) == 1);
  ADT_sl_list_pop(list, (void *)&tmp);
  free(tmp);
  assert(ADT_sl_list_length(list) == 0);

  printf("Test Single Linked List Length (ADT_sl_list_length)...ok\n");
  ADT_sl_list_destroy(list, &free);
  free(list);
}

int main()
{
  test__ADT_sl_list_push();
  test__ADT_sl_list_pop();
  test__ADT_sl_list_append();
  test__ADT_sl_list_insert_after();
  test__ADT_sl_list_remove_after();
  test__ADT_sl_list_length();
  return 0;
}
